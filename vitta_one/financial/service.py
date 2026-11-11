"""Authorized financial operations with durable intentions and optimistic reconciliation."""
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from vitta_one.auth.authorization import require_authenticated, PasswordChangeRequiredError
from vitta_one.auth.roles import Role
from vitta_one.appointment_scheduling.settings import clinic_timezone
from vitta_one.models.appointment import Consultation
from vitta_one.models.patient_queue import Patient
from vitta_one.models.financial import FinancialCustomer, FinancialCharge, FinancialChange, FinancialWebhookEvent, now
from .asaas import AsaasClient, FinancialError, ProviderUnknown, ProviderRejected, amount, payment_url, resource_id

STATES = {"PENDING": "PENDING", "CONFIRMED": "CONFIRMED", "RECEIVED": "RECEIVED", "OVERDUE": "OVERDUE",
          "REFUNDED": "REFUNDED", "REFUND_IN_PROGRESS": "REFUND_PENDING", "REFUND_REQUESTED": "REFUND_PENDING"}
ACTIVE = ("CANCELLED", "REFUNDED")


class ReconcileConflict(FinancialError):
    pass


def authorize(db: Session, token: str, *, admin=False):
    identity = require_authenticated(db, token)
    if identity.must_change_password:
        raise PasswordChangeRequiredError("Troca de senha inicial obrigatória.")
    allowed = {Role.ADMINISTRADOR} if admin else {Role.ADMINISTRADOR, Role.FINANCEIRO}
    if identity.role not in allowed:
        raise PermissionError("Acesso financeiro não autorizado.")
    return identity


def _locked(db: Session, model, identifier: int):
    row = db.exec(select(model).where(model.id == identifier).with_for_update().execution_options(populate_existing=True)).first()
    if row is None:
        raise FinancialError("Registro financeiro não encontrado.")
    return row


def _history(db: Session, charge: FinancialCharge, status: str, source: str, *, key=None, actor=None, reason=""):
    before = charge.status
    charge.status = status
    charge.revision += 1
    charge.updated_at = now()
    entry = FinancialChange(charge_id=charge.id, event_key=key or uuid4().hex,
                            previous_status=before, status=status, source=source, actor_id=actor, reason=reason[:240])
    db.add(entry)
    db.add(charge)
    db.flush()
    if status == "RECEIVED" and before != "RECEIVED":
        from vitta_one.notifications.service import enqueue_financial
        enqueue_financial(db, charge, "payment_received", entry.id)


def _customer(db: Session, patient: Patient, client: AsaasClient) -> FinancialCustomer:
    # Serialize callers from different consultations of the same patient.
    _locked(db, Patient, patient.id)
    customer = db.exec(select(FinancialCustomer).where(FinancialCustomer.patient_id == patient.id).with_for_update()).first()
    if customer is None:
        customer = FinancialCustomer(patient_id=patient.id)
        db.add(customer)
        db.flush()
    if customer.provider_id:
        db.commit()
        return customer
    if customer.status != "NEW":
        db.commit()
        raise FinancialError("Cliente financeiro aguardando conciliação. Não repita a emissão.")
    customer.status = "SENDING"
    customer.updated_at = now()
    db.add(customer)
    db.commit()
    try:
        rows = client.find("customers", customer.reference)
        if len(rows) > 1:
            raise FinancialError("Vínculo externo ambíguo; revisão necessária.")
        if not rows and client.find("customers", patient.cpf, query_field="cpfCnpj"):
            raise FinancialError("Já existe cliente Asaas para este CPF sem vínculo inequívoco. Revise o cadastro externo antes de continuar.")
        data = rows[0] if rows else client.create_customer(name=patient.name, cpf=patient.cpf, reference=customer.reference)
        if data.get("cpfCnpj") != patient.cpf or data.get("externalReference") != customer.reference:
            raise FinancialError("Cadastro externo divergente; revisão necessária.")
        provider_id = resource_id(data.get("id"))
    except (FinancialError, ValueError):
        customer.status = "UNKNOWN"
        db.add(customer)
        db.commit()
        raise
    customer.provider_id = provider_id
    customer.status = "READY"
    customer.updated_at = now()
    db.add(customer)
    db.commit()
    return customer


def sync_customer(db: Session, *, token: str, patient_id: int, client: AsaasClient | None = None):
    authorize(db, token)
    client = client or AsaasClient.from_env()
    patient = _locked(db, Patient, patient_id)
    customer = db.exec(select(FinancialCustomer).where(FinancialCustomer.patient_id == patient_id).with_for_update()).first()
    if customer is None:
        raise FinancialError("Paciente ainda não possui vínculo financeiro.")
    updated = customer.updated_at.replace(tzinfo=timezone.utc) if customer.updated_at.tzinfo is None else customer.updated_at
    if customer.status == "SENDING" and updated > now() - timedelta(minutes=2):
        raise FinancialError("Operação em andamento; consulte novamente após revisão.")
    db.commit()
    rows = client.find("customers", customer.reference)
    if len(rows) != 1 or rows[0].get("cpfCnpj") != patient.cpf:
        raise FinancialError("Cliente não localizado de forma inequívoca. Não crie outro automaticamente.")
    customer.provider_id = resource_id(rows[0].get("id"))
    data = client.update_customer(customer.provider_id, name=patient.name, cpf=patient.cpf)
    if data.get("id") != customer.provider_id:
        raise ProviderUnknown()
    customer.status = "READY"
    customer.updated_at = now()
    db.add(customer)
    db.commit()
    return customer


def create_charge(db: Session, *, token: str, consultation_id: int, value: object, due_date: date,
                  method: str, client: AsaasClient | None = None) -> FinancialCharge:
    identity = authorize(db, token)
    value = amount(value)
    if not isinstance(due_date, date) or due_date < now().astimezone(clinic_timezone()).date():
        raise FinancialError("Informe vencimento de hoje ou futuro.")
    if method not in {"PIX", "BOLETO"}:
        raise FinancialError("Método não homologado. Utilize Pix ou boleto.")
    client = client or AsaasClient.from_env()
    consultation = _locked(db, Consultation, consultation_id)
    if consultation.status == "CANCELADA":
        raise FinancialError("Não é possível emitir cobrança para Consulta cancelada.")
    if db.exec(select(FinancialCharge.id).where(FinancialCharge.consultation_id == consultation_id,
                                              FinancialCharge.status.not_in(ACTIVE))).first():
        raise FinancialError("A Consulta já possui cobrança ativa ou emissão em revisão.")
    patient = _locked(db, Patient, consultation.patient_id)
    db.commit()
    customer = _customer(db, patient, client)
    consultation = _locked(db, Consultation, consultation_id)
    if consultation.status == "CANCELADA":
        raise FinancialError("A Consulta foi cancelada durante a emissão.")
    # The unique index closes the gap between external customer resolution and charge creation.
    charge = FinancialCharge(consultation_id=consultation_id, customer_id=customer.id, created_by=identity.id,
                             value=value, due_date=due_date, method=method, status="SENDING", operation="CREATE")
    db.add(charge)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise FinancialError("A Consulta já possui cobrança ativa ou emissão em revisão.") from None
    try:
        data = client.create_payment(customer_id=customer.provider_id, billing_type=method, value=value,
                                     due_date=due_date, reference=charge.reference)
        _apply_snapshot(db, charge.id, data, expected_revision=charge.revision, source="CREATE", actor=identity.id)
        charge = db.get(FinancialCharge, charge.id)
        charge.operation = ""
        db.add(charge)
        db.commit()
        return charge
    except (FinancialError, IntegrityError):
        db.rollback()
        charge = _locked(db, FinancialCharge, charge.id)
        _history(db, charge, "UNKNOWN", "CREATE", actor=identity.id)
        db.commit()
        raise


def _apply_snapshot(db: Session, charge_id: int, data: dict, *, expected_revision: int, source: str,
                    actor=None, event_key=None):
    charge = _locked(db, FinancialCharge, charge_id)
    if charge.revision != expected_revision:
        raise ReconcileConflict("A cobrança mudou durante a consulta; concilie novamente.")
    customer = db.get(FinancialCustomer, charge.customer_id)
    provider_id = resource_id(data.get("id"))
    if (data.get("externalReference") != charge.reference or data.get("customer") != customer.provider_id
            or amount(data.get("value")) != charge.value or data.get("billingType") != charge.method
            or (charge.provider_id and charge.provider_id != provider_id)):
        raise FinancialError("Dados financeiros divergentes; revisão necessária.")
    state = "CANCELLED" if data.get("deleted") is True else STATES.get(data.get("status"), "REVIEW")
    if data.get("refunds") and state not in {"REFUNDED", "REFUND_PENDING"}:
        # Partial refunds are outside the initial operational scope.
        state = "REVIEW"
    newly_linked = charge.provider_id is None
    charge.provider_id = provider_id
    charge.provider_status = str(data.get("status", "UNKNOWN"))[:48]
    charge.invoice_url = payment_url(data.get("invoiceUrl"))
    charge.boleto_url = payment_url(data.get("bankSlipUrl"))
    if state == "RECEIVED" and charge.received_at is None:
        received = data.get("paymentDate") or data.get("clientPaymentDate")
        try:
            charge.received_at = datetime.combine(date.fromisoformat(received), datetime.min.time(), tzinfo=clinic_timezone()).astimezone(timezone.utc)
        except (ValueError, TypeError):
            charge.received_at = now()
    if state != charge.status:
        _history(db, charge, state, source, key=event_key, actor=actor)
    else:
        charge.revision += 1
        charge.updated_at = now()
        db.add(charge)
    if newly_linked and (charge.invoice_url or charge.boleto_url):
        from vitta_one.notifications.service import enqueue_financial
        enqueue_financial(db, charge, "charge_available", charge.id)
    if (charge.operation.startswith("CANCEL") and state == "CANCELLED") or (charge.operation.startswith("REFUND") and state == "REFUNDED"):
        charge.operation = ""
    return charge


def reconcile(db: Session, *, token: str, charge_id: int, client: AsaasClient | None = None):
    authorize(db, token)
    return _reconcile(db, charge_id, client or AsaasClient.from_env())


def _reconcile(db: Session, charge_id: int, client: AsaasClient, *, event=None):
    charge = _locked(db, FinancialCharge, charge_id)
    revision, provider_id, reference = charge.revision, charge.provider_id, charge.reference
    db.commit()
    if provider_id:
        data = client.payment(provider_id)
    else:
        rows = client.find("payments", reference)
        if len(rows) != 1:
            raise FinancialError("Cobrança não localizada de forma inequívoca. Não repita a emissão.")
        data = rows[0]
    charge = _apply_snapshot(db, charge_id, data, expected_revision=revision, source="WEBHOOK" if event else "RECONCILE",
                             event_key=event.event_id if event else None)
    if event:
        event.status = "PROCESSED"
        event.error_code = ""
        db.add(event)
    db.commit()
    return charge


def mutate_charge(db: Session, *, token: str, charge_id: int, operation: str, reason: str,
                  client: AsaasClient | None = None):
    if operation not in {"CANCEL", "REFUND"}:
        raise FinancialError("Operação inválida.")
    identity = authorize(db, token, admin=operation == "REFUND")
    if not 3 <= len(reason.strip()) <= 240:
        raise FinancialError("Informe um motivo entre 3 e 240 caracteres, sem dados clínicos.")
    client = client or AsaasClient.from_env()
    _reconcile(db, charge_id, client)
    charge = _locked(db, FinancialCharge, charge_id)
    if charge.operation and charge.operation != "CREATE":
        raise FinancialError("Operação anterior aguardando conciliação; não repita.")
    if operation == "CANCEL" and charge.status not in {"PENDING", "OVERDUE"}:
        raise FinancialError("Somente cobranças pendentes ou vencidas podem ser canceladas.")
    if operation == "REFUND" and (charge.status != "RECEIVED" or charge.method != "PIX"):
        raise FinancialError("Estorno homologado somente para Pix recebido.")
    charge.operation = operation + "_UNKNOWN"
    _history(db, charge, charge.status, operation + "_REQUESTED", actor=identity.id, reason=reason)
    db.commit()
    try:
        if operation == "CANCEL":
            result = client.cancel(charge.provider_id)
            if result.get("deleted") is not True:
                raise ProviderUnknown()
            charge = _locked(db, FinancialCharge, charge_id)
            _history(db, charge, "CANCELLED", "CANCEL_CONFIRMED", actor=identity.id)
            charge.operation = ""
            db.add(charge)
            db.commit()
            return charge
        else:
            client.refund(charge.provider_id)
    except ProviderRejected:
        charge.operation = ""
        _history(db, charge, charge.status, operation + "_REJECTED", actor=identity.id)
        db.commit()
        raise
    return _reconcile(db, charge_id, client)


def pix_data(db: Session, *, token: str, charge_id: int, client: AsaasClient | None = None) -> dict:
    authorize(db, token)
    charge = db.get(FinancialCharge, charge_id)
    if charge is None or charge.method != "PIX" or not charge.provider_id or charge.status not in {"PENDING", "OVERDUE"}:
        raise FinancialError("Pix indisponível para esta cobrança.")
    return (client or AsaasClient.from_env()).pix(charge.provider_id)


def process_events(db: Session, *, client: AsaasClient | None = None, limit=20) -> int:
    client = client or AsaasClient.from_env()
    processed = 0
    for _ in range(min(max(limit, 1), 100)):
        event = db.exec(select(FinancialWebhookEvent).where(
            FinancialWebhookEvent.status.in_(["PENDING", "PROCESSING"]),
            FinancialWebhookEvent.next_attempt_at <= now(),
            (FinancialWebhookEvent.lease_until.is_(None)) | (FinancialWebhookEvent.lease_until < now()),
        ).order_by(FinancialWebhookEvent.id).with_for_update(skip_locked=True).limit(1)).first()
        if event is None:
            db.rollback()
            break
        event.status = "PROCESSING"
        event.lease_until = now() + timedelta(minutes=2)
        event.attempts += 1
        db.add(event)
        db.commit()
        try:
            charge_id = db.exec(select(FinancialCharge.id).where(FinancialCharge.provider_id == event.payment_id)).first()
            if charge_id is None:
                raise FinancialError("Cobrança não vinculada.")
            _reconcile(db, charge_id, client, event=event)
            processed += 1
        except FinancialError as exc:
            db.rollback()
            event = db.get(FinancialWebhookEvent, event.id)
            event.status = "PENDING" if isinstance(exc, (ProviderUnknown, ReconcileConflict)) and event.attempts < 10 else "REVIEW"
            event.error_code = type(exc).__name__
            backoff = min(900, 30 * 2 ** min(event.attempts, 5))
            event.next_attempt_at = now() + timedelta(seconds=max(backoff, getattr(exc, "retry_after", 0)))
            event.lease_until = None
            db.add(event)
            db.commit()
    return processed
