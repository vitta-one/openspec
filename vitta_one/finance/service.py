"""Financial catalog, accounts, billing and webhook reconciliation."""

from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
from typing import Iterable

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlmodel import Session, select

from vitta_one.integrations.asaas import AsaasClient, AsaasUnavailableError
from vitta_one.integrations.settings import asaas_settings
from vitta_one.models.finance import (
    BillingCharge, BillingCustomer, BillingWebhookEvent, FinancialAudit,
    FinancialService, PatientAccount, PatientAccountItem, PaymentRecord,
)
from vitta_one.models.appointment import Consultation
from vitta_one.models.patient_queue import Patient


class FinanceError(ValueError):
    pass


class FinanceNotConfiguredError(FinanceError):
    pass


class FinanceAuthorizationError(PermissionError):
    pass


class FinanceNotFoundError(LookupError):
    pass


class FinanceConflictError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class ServiceView:
    id: int
    name: str
    description: str
    unit_price_cents: int
    active: bool


@dataclass(frozen=True, slots=True)
class AccountItemInput:
    service_id: int
    quantity: int


@dataclass(frozen=True, slots=True)
class AccountView:
    id: int
    patient_id: int
    patient_name: str
    status: str
    due_date: date
    total_cents: int
    paid_cents: int
    balance_cents: int
    charge_id: int
    charge_status: str
    invoice_url: str


@dataclass(frozen=True, slots=True)
class DashboardView:
    open_cents: int
    overdue_cents: int
    received_cents: int
    account_count: int


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _clean(value: str, *, label: str, limit: int) -> str:
    result = " ".join(str(value or "").split())
    if not result:
        raise FinanceError(f"Informe {label}.")
    if len(result) > limit:
        raise FinanceError(f"{label.capitalize()} excede o limite de {limit} caracteres.")
    return result


def _service_view(row: FinancialService) -> ServiceView:
    if row.id is None:
        raise RuntimeError("Serviço persistido sem identificador.")
    return ServiceView(row.id, row.name, row.description, row.unit_price_cents, row.active)


def create_service(db: Session, *, actor_user_id: int, name: str, description: str, unit_price_cents: int) -> ServiceView:
    clean_name = _clean(name, label="o nome", limit=160)
    clean_description = " ".join(str(description or "").split())
    if len(clean_description) > 2_000:
        raise FinanceError("A descrição excede o limite de 2000 caracteres.")
    if not isinstance(unit_price_cents, int) or isinstance(unit_price_cents, bool) or unit_price_cents <= 0:
        raise FinanceError("O preço deve ser informado em centavos e ser positivo.")
    row = FinancialService(
        name=clean_name, description=clean_description, unit_price_cents=unit_price_cents,
        active=True, created_by_user_id=actor_user_id, updated_by_user_id=actor_user_id,
    )
    db.add(row)
    try:
        db.flush()
        db.add(FinancialAudit(resource_type="SERVICE", resource_id=row.id, actor_user_id=actor_user_id, action="CREATE", outcome="SUCCESS"))
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise FinanceConflictError("Já existe um serviço com este nome.") from exc
    db.refresh(row)
    return _service_view(row)


def set_service_active(db: Session, *, actor_user_id: int, service_id: int, active: bool) -> ServiceView:
    row = db.exec(select(FinancialService).where(FinancialService.id == service_id).with_for_update()).first()
    if row is None:
        raise FinanceNotFoundError("O serviço não está disponível.")
    row.active = bool(active)
    row.updated_by_user_id = actor_user_id
    row.updated_at = utc_now()
    db.add(row)
    db.add(FinancialAudit(resource_type="SERVICE", resource_id=row.id, actor_user_id=actor_user_id, action="ACTIVATE" if active else "DEACTIVATE", outcome="SUCCESS"))
    db.commit()
    db.refresh(row)
    return _service_view(row)


def list_services(db: Session, *, include_inactive: bool = False) -> tuple[ServiceView, ...]:
    stmt = select(FinancialService)
    if not include_inactive:
        stmt = stmt.where(FinancialService.active.is_(True))
    rows = db.exec(stmt.order_by(FinancialService.name)).all()
    return tuple(_service_view(row) for row in rows)


def issue_account(
    db: Session,
    *,
    actor_user_id: int,
    patient_id: int,
    due_date: date,
    items: Iterable[AccountItemInput],
    consultation_id: int | None = None,
) -> AccountView:
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise FinanceNotFoundError("O Paciente não está disponível.")
    if due_date < date.today():
        raise FinanceError("O vencimento não pode estar no passado.")
    if consultation_id is not None:
        consultation = db.get(Consultation, consultation_id)
        if consultation is None or consultation.patient_id != patient_id:
            raise FinanceError("A consulta informada não pertence ao Paciente.")
    inputs = list(items)
    if not inputs or len(inputs) > 50:
        raise FinanceError("Informe entre 1 e 50 itens para a conta.")
    service_ids = {item.service_id for item in inputs}
    services = {row.id: row for row in db.exec(select(FinancialService).where(FinancialService.id.in_(service_ids), FinancialService.active.is_(True))).all()}
    if len(services) != len(service_ids):
        raise FinanceError("Um ou mais serviços não estão disponíveis.")
    total = 0
    lines: list[tuple[FinancialService, int, int]] = []
    for item in inputs:
        if not isinstance(item.quantity, int) or isinstance(item.quantity, bool) or not 1 <= item.quantity <= 100:
            raise FinanceError("A quantidade deve estar entre 1 e 100.")
        service = services[item.service_id]
        line_total = service.unit_price_cents * item.quantity
        total += line_total
        lines.append((service, item.quantity, line_total))
    account = PatientAccount(
        patient_id=patient_id, consultation_id=consultation_id,
        issued_by_user_id=actor_user_id, due_date=due_date,
        total_cents=total, paid_cents=0, status="OPEN",
    )
    db.add(account)
    try:
        db.flush()
        for service, quantity, line_total in lines:
            db.add(PatientAccountItem(
                account_id=account.id, service_id=service.id,
                description_snapshot=service.name, quantity=quantity,
                unit_price_cents=service.unit_price_cents, total_cents=line_total,
            ))
        db.add(FinancialAudit(resource_type="ACCOUNT", resource_id=account.id, actor_user_id=actor_user_id, action="ISSUE", outcome="SUCCESS"))
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise FinanceConflictError("Não foi possível emitir a conta.") from exc
    db.refresh(account)
    return _account_view(db, account, patient.name)


def _account_view(db: Session, account: PatientAccount, patient_name: str | None = None) -> AccountView:
    if account.id is None:
        raise RuntimeError("Conta persistida sem identificador.")
    if patient_name is None:
        patient = db.get(Patient, account.patient_id)
        patient_name = patient.name if patient else "Paciente indisponível"
    charge = db.exec(select(BillingCharge).where(BillingCharge.account_id == account.id).order_by(BillingCharge.created_at.desc())).first()
    return AccountView(
        id=account.id, patient_id=account.patient_id, patient_name=patient_name,
        status=account.status, due_date=account.due_date, total_cents=account.total_cents,
        paid_cents=account.paid_cents, balance_cents=max(0, account.total_cents - account.paid_cents),
        charge_id=charge.id if charge and charge.id is not None else 0,
        charge_status=charge.status if charge else "NOT_ISSUED",
        invoice_url=charge.invoice_url or "" if charge else "",
    )


def list_accounts(db: Session) -> tuple[AccountView, ...]:
    rows = db.exec(select(PatientAccount).order_by(PatientAccount.created_at.desc(), PatientAccount.id.desc())).all()
    return tuple(_account_view(db, row) for row in rows)


def list_patient_accounts(db: Session, *, patient_user_id: int) -> tuple[AccountView, ...]:
    patient = db.exec(select(Patient).where(Patient.user_id == patient_user_id)).first()
    if patient is None:
        raise FinanceAuthorizationError("O acesso ao portal não possui vínculo financeiro.")
    rows = db.exec(select(PatientAccount).where(PatientAccount.patient_id == patient.id).order_by(PatientAccount.created_at.desc())).all()
    return tuple(_account_view(db, row, patient.name) for row in rows)


_ASAAS_TO_LOCAL = {
    "PENDING": "PENDING", "RECEIVED": "RECEIVED", "CONFIRMED": "CONFIRMED",
    "OVERDUE": "OVERDUE", "REFUNDED": "REFUNDED", "REFUND_REQUESTED": "REFUNDED",
}


def create_charge(db: Session, *, actor_user_id: int, account_id: int, billing_type: str, client: AsaasClient | None = None) -> AccountView:
    billing_type = str(billing_type or "").upper()
    if billing_type not in {"UNDEFINED", "BOLETO", "PIX", "CREDIT_CARD"}:
        raise FinanceError("A forma de pagamento é inválida.")
    account = db.exec(select(PatientAccount).where(PatientAccount.id == account_id).with_for_update()).first()
    if account is None:
        raise FinanceNotFoundError("A conta não está disponível.")
    if account.status in {"PAID", "CANCELLED"}:
        raise FinanceConflictError("Esta conta não aceita nova cobrança.")
    existing = db.exec(select(BillingCharge).where(BillingCharge.account_id == account.id).order_by(BillingCharge.created_at.desc()).with_for_update()).first()
    if existing is not None:
        return _account_view(db, account)
    patient = db.get(Patient, account.patient_id)
    if patient is None:
        raise FinanceNotFoundError("O Paciente não está disponível.")
    settings = asaas_settings()
    if settings is None:
        raise FinanceNotConfiguredError("A integração financeira ainda não está configurada.")
    request_key = hashlib.sha256(f"account:{account.id}".encode()).hexdigest()
    external_reference = f"vitta-account-{account.id}"
    charge = BillingCharge(
        account_id=account.id, request_key=request_key, external_reference=external_reference,
        billing_type=billing_type, status="CREATING", due_date=account.due_date,
        value_cents=account.total_cents - account.paid_cents,
    )
    db.add(charge)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return _account_view(db, db.get(PatientAccount, account_id))
    db.refresh(charge)
    provider = client or AsaasClient(settings)
    try:
        customer = db.exec(select(BillingCustomer).where(BillingCustomer.patient_id == patient.id)).first()
        if customer is None:
            external_patient = f"vitta-patient-{patient.id}"
            remote_customer = provider.find_customer(external_patient) or provider.create_customer(
                name=patient.name,
                cpf_cnpj=patient.cpf,
                external_reference=external_patient,
            )
            customer = BillingCustomer(patient_id=patient.id, provider_customer_id=remote_customer.id)
            db.add(customer)
            db.commit()
        remote_charge = provider.find_charge(external_reference)
        if remote_charge is None:
            remote_charge = provider.create_charge(
                customer_id=customer.provider_customer_id, billing_type=billing_type,
                value_cents=charge.value_cents, due_date=charge.due_date,
                description=f"Conta Vitta One {account.id}", external_reference=external_reference,
            )
    except AsaasUnavailableError:
        locked = db.exec(select(BillingCharge).where(BillingCharge.id == charge.id).with_for_update()).one()
        locked.status = "RECONCILIATION_REQUIRED"
        locked.status_detail_code = "CREATE_RESULT_UNKNOWN"
        locked.updated_at = utc_now()
        db.add(locked)
        db.commit()
        raise
    locked = db.exec(select(BillingCharge).where(BillingCharge.id == charge.id).with_for_update()).one()
    locked.provider_charge_id = remote_charge.id
    locked.status = _ASAAS_TO_LOCAL.get(remote_charge.status.upper(), "PENDING")
    locked.invoice_url = remote_charge.invoice_url
    locked.last_provider_sync_at = utc_now()
    locked.updated_at = locked.last_provider_sync_at
    db.add(locked)
    db.add(FinancialAudit(resource_type="CHARGE", resource_id=locked.id, actor_user_id=actor_user_id, action="CREATE", outcome="SUCCESS"))
    db.commit()
    db.refresh(account)
    return _account_view(db, account, patient.name)


def reconcile_charge(
    db: Session,
    *,
    actor_user_id: int,
    charge_id: int,
    client: AsaasClient | None = None,
) -> AccountView:
    """Safely query an uncertain Asaas creation without issuing a duplicate charge."""
    charge = db.exec(
        select(BillingCharge).where(BillingCharge.id == charge_id).with_for_update()
    ).first()
    if charge is None:
        raise FinanceNotFoundError("A cobrança não está disponível.")
    account = db.get(PatientAccount, charge.account_id)
    if account is None:
        raise FinanceNotFoundError("A conta não está disponível.")
    if charge.status != "RECONCILIATION_REQUIRED":
        return _account_view(db, account)
    if client is None:
        settings = asaas_settings()
        if settings is None:
            raise FinanceNotConfiguredError("A integração financeira ainda não está configurada.")
        provider = AsaasClient(settings)
    else:
        provider = client
    remote = provider.find_charge(charge.external_reference)
    if remote is None:
        charge.last_provider_sync_at = utc_now()
        charge.updated_at = charge.last_provider_sync_at
        charge.status_detail_code = "REMOTE_NOT_FOUND"
        db.add(charge)
        db.add(FinancialAudit(
            resource_type="CHARGE", resource_id=charge.id,
            actor_user_id=actor_user_id, action="RECONCILE",
            outcome="PENDING", detail_code="REMOTE_NOT_FOUND",
        ))
        db.commit()
        raise FinanceConflictError(
            "A cobrança ainda não foi localizada no Asaas. Nenhuma duplicata foi criada."
        )
    charge.provider_charge_id = remote.id
    charge.status = _ASAAS_TO_LOCAL.get(remote.status.upper(), "PENDING")
    charge.invoice_url = remote.invoice_url
    charge.status_detail_code = ""
    charge.last_provider_sync_at = utc_now()
    charge.updated_at = charge.last_provider_sync_at
    db.add(charge)
    db.add(FinancialAudit(
        resource_type="CHARGE", resource_id=charge.id,
        actor_user_id=actor_user_id, action="RECONCILE", outcome="SUCCESS",
    ))
    db.commit()
    return _account_view(db, account)


def cancel_charge(db: Session, *, actor_user_id: int, charge_id: int, client: AsaasClient | None = None) -> None:
    charge = db.exec(select(BillingCharge).where(BillingCharge.id == charge_id).with_for_update()).first()
    if charge is None:
        raise FinanceNotFoundError("A cobrança não está disponível.")
    if charge.status in {"RECEIVED", "CONFIRMED", "REFUNDED"}:
        raise FinanceConflictError("Esta cobrança não pode ser cancelada neste estado.")
    if charge.status == "CANCELLED":
        return
    if not charge.provider_charge_id:
        raise FinanceConflictError("A cobrança precisa ser reconciliada antes do cancelamento.")
    settings = asaas_settings()
    if settings is None:
        raise FinanceNotConfiguredError("A integração financeira ainda não está configurada.")
    provider = client or AsaasClient(settings)
    provider.cancel_charge(charge.provider_charge_id)
    charge.status = "CANCELLED"
    charge.updated_at = utc_now()
    db.add(charge)
    db.add(FinancialAudit(resource_type="CHARGE", resource_id=charge.id, actor_user_id=actor_user_id, action="CANCEL", outcome="SUCCESS"))
    db.commit()


def _money_to_cents(value) -> int:
    try:
        decimal = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError) as exc:
        raise FinanceError("Valor de webhook inválido.") from exc
    cents = int(decimal * 100)
    if cents <= 0:
        raise FinanceError("Valor de webhook inválido.")
    return cents


def process_asaas_webhook(db: Session, payload: dict) -> str:
    if not isinstance(payload, dict):
        raise FinanceError("Payload de webhook inválido.")
    event_id = str(payload.get("id") or "").strip()
    event_type = str(payload.get("event") or "").strip().upper()
    payment = payload.get("payment")
    if not event_id or len(event_id) > 160 or not event_type or not isinstance(payment, dict):
        raise FinanceError("Payload de webhook inválido.")
    if db.exec(select(BillingWebhookEvent.id).where(BillingWebhookEvent.event_id == event_id)).first() is not None:
        return "DUPLICATE"
    provider_charge_id = str(payment.get("id") or "").strip()
    event = BillingWebhookEvent(event_id=event_id, event_type=event_type, provider_charge_id=provider_charge_id or None)
    db.add(event)
    charge = db.exec(select(BillingCharge).where(BillingCharge.provider_charge_id == provider_charge_id).with_for_update()).first()
    if charge is None:
        event.outcome = "UNKNOWN_CHARGE"
    else:
        provider_status = str(payment.get("status") or "").upper()
        local_status = _ASAAS_TO_LOCAL.get(provider_status)
        if local_status:
            charge.status = local_status
            charge.updated_at = utc_now()
            charge.last_provider_sync_at = charge.updated_at
            db.add(charge)
        if event_type in {"PAYMENT_RECEIVED", "PAYMENT_CONFIRMED"}:
            amount = _money_to_cents(payment.get("value"))
            record = db.exec(select(PaymentRecord).where(PaymentRecord.provider_payment_id == provider_charge_id).with_for_update()).first()
            if record is None:
                record = PaymentRecord(
                    charge_id=charge.id, provider_payment_id=provider_charge_id,
                    provider_event_id=event_id, amount_cents=amount,
                    status="CONFIRMED" if event_type == "PAYMENT_CONFIRMED" else "RECEIVED",
                    paid_at=utc_now(),
                )
            else:
                record.provider_event_id = event_id
                record.amount_cents = amount
                record.status = "CONFIRMED" if event_type == "PAYMENT_CONFIRMED" else record.status
                record.paid_at = record.paid_at or utc_now()
            db.add(record)
            db.flush()
            account = db.exec(select(PatientAccount).where(PatientAccount.id == charge.account_id).with_for_update()).one()
            paid = sum(
                row.amount_cents for row in db.exec(
                    select(PaymentRecord).join(BillingCharge, BillingCharge.id == PaymentRecord.charge_id).where(
                        BillingCharge.account_id == account.id,
                        PaymentRecord.status.in_(["RECEIVED", "CONFIRMED"]),
                    )
                ).all()
            )
            account.paid_cents = min(account.total_cents, paid)
            account.status = "PAID" if account.paid_cents >= account.total_cents else "PARTIALLY_PAID"
            account.updated_at = utc_now()
            db.add(account)
        elif event_type in {"PAYMENT_REFUNDED", "PAYMENT_CHARGEBACK_REQUESTED"}:
            record = db.exec(select(PaymentRecord).where(PaymentRecord.provider_payment_id == provider_charge_id).with_for_update()).first()
            if record is not None:
                record.provider_event_id = event_id
                record.status = "REFUNDED" if event_type == "PAYMENT_REFUNDED" else "CHARGEBACK"
                db.add(record)
                db.flush()
                account = db.exec(select(PatientAccount).where(PatientAccount.id == charge.account_id).with_for_update()).one()
                paid = sum(
                    row.amount_cents for row in db.exec(
                        select(PaymentRecord).join(BillingCharge, BillingCharge.id == PaymentRecord.charge_id).where(
                            BillingCharge.account_id == account.id,
                            PaymentRecord.status.in_(["RECEIVED", "CONFIRMED"]),
                        )
                    ).all()
                )
                account.paid_cents = min(account.total_cents, paid)
                account.status = "OPEN" if account.paid_cents == 0 else ("PAID" if account.paid_cents >= account.total_cents else "PARTIALLY_PAID")
                account.updated_at = utc_now()
                db.add(account)
        event.outcome = "PROCESSED" if local_status or event_type.startswith("PAYMENT_") else "IGNORED"
    event.processed_at = utc_now()
    db.add(event)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return "DUPLICATE"
    except SQLAlchemyError as exc:
        db.rollback()
        raise FinanceConflictError("Não foi possível processar o evento financeiro.") from exc
    return event.outcome


def dashboard(db: Session, *, today: date | None = None) -> DashboardView:
    current = today or date.today()
    rows = db.exec(select(PatientAccount).where(PatientAccount.status != "CANCELLED")).all()
    open_cents = sum(max(0, row.total_cents - row.paid_cents) for row in rows)
    overdue_cents = sum(max(0, row.total_cents - row.paid_cents) for row in rows if row.due_date < current and row.status != "PAID")
    received_cents = sum(row.paid_cents for row in rows)
    return DashboardView(open_cents, overdue_cents, received_cents, len(rows))

