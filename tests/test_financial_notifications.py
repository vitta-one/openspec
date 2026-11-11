"""Persisted financial and outbox behavior with mocked providers, not real Sandbox."""
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import json
import os
import base64
from uuid import uuid4
from contextlib import contextmanager

import httpx
import pytest
from sqlalchemy.pool import StaticPool
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError
from sqlmodel import SQLModel, Session, create_engine, select
from starlette.applications import Starlette
from starlette.testclient import TestClient

import vitta_one.models
from vitta_one.auth.roles import Role
from vitta_one.auth.service import create_session
from vitta_one.models.auth import User
from vitta_one.models.patient_queue import Patient
from vitta_one.models.professional import Professional
from vitta_one.models.appointment import Consultation, ProfessionalAvailabilitySlot
from vitta_one.models.financial import FinancialCharge, FinancialCustomer, FinancialChange, FinancialWebhookEvent
from vitta_one.models.notification import EmailNotification, EmailAttempt, EmailWebhookEvent, NotificationPreferenceChange
from vitta_one.financial import service as financial
from vitta_one.financial.asaas import AsaasClient, FinancialError, ProviderUnknown
from vitta_one.notifications import service as mail
from vitta_one.notifications.resend import EmailDelivery
from vitta_one.notifications.templates import render
from vitta_one.integration_api import provider_routes


@pytest.fixture(params=["sqlite", "postgresql"])
def setup(monkeypatch, request):
    monkeypatch.setenv("VITTA_ONE_CLINIC_TIMEZONE", "America/Sao_Paulo")
    monkeypatch.setenv("VITTA_ONE_PUBLIC_URL", "https://vitta.example.test")
    if request.param == "postgresql":
        url = os.getenv("DATABASE_URL", "")
        if not url.startswith("postgresql") or os.getenv("VITTA_ONE_QA_DISPOSABLE_DATABASE") != "yes":
            pytest.skip("PostgreSQL requires an explicitly disposable test database.")
        schema = "vitta_integrations_" + uuid4().hex
        from sqlalchemy import text
        admin_engine = create_engine(url)
        with admin_engine.begin() as conn:
            conn.execute(text(f'CREATE SCHEMA "{schema}"'))
        engine = create_engine(url, connect_args={"options": f"-csearch_path={schema}"})
    else:
        engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        @event.listens_for(engine, "connect")
        def enforce_foreign_keys(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as db:
        tokens, users = {}, {}
        for role in Role:
            user = User(email=f"{role.value.lower()}@example.test", password_hash="test-no-login", role=role.value)
            db.add(user)
            db.flush()
            users[role] = user.id
            tokens[role] = create_session(db, user_id=user.id, ttl=timedelta(hours=2))
        patient = Patient(name="Paciente Teste", cpf="52998224725", user_id=users[Role.PACIENTE])
        professional = Professional(name="Médico Teste", registration_identifier="INT-TEST", is_active=True)
        db.add(patient)
        db.add(professional)
        db.flush()
        future = datetime.now(timezone.utc) + timedelta(days=2)
        slot = ProfessionalAvailabilitySlot(professional_id=professional.id, starts_at=future)
        db.add(slot)
        db.flush()
        consultation = Consultation(patient_id=patient.id, professional_id=professional.id, availability_slot_id=slot.id, scheduled_at=future)
        db.add(consultation)
        db.commit()
        yield db, tokens, patient, consultation, engine
    engine.dispose()
    if request.param == "postgresql":
        with admin_engine.begin() as conn:
            conn.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        admin_engine.dispose()


class Provider:
    def __init__(self):
        self.customers, self.payments, self.calls = [], [], []
        self.timeout = False
        self.reject_refund = False

    def handle(self, request):
        self.calls.append((request.method, request.url.path))
        path = request.url.path
        body = json.loads(request.content) if request.content else {}
        if request.method == "GET" and path.endswith("/customers"):
            return httpx.Response(200, json={"data": self.customers, "hasMore": False})
        if request.method == "POST" and path.endswith("/customers"):
            data = {**body, "id": "cus_test"}
            self.customers.append(data)
            return httpx.Response(200, json=data)
        if request.method == "PUT" and "/customers/" in path:
            self.customers[0].update(body)
            return httpx.Response(200, json=self.customers[0])
        if request.method == "POST" and path.endswith("/payments"):
            data = {**body, "id": "pay_test", "status": "PENDING", "invoiceUrl": "https://sandbox.asaas.com/i/test"}
            self.payments.append(data)
            if self.timeout:
                raise httpx.ReadTimeout("Controlled test")
            return httpx.Response(200, json=data)
        if request.method == "GET" and path.endswith("/payments"):
            return httpx.Response(200, json={"data": self.payments, "hasMore": False})
        if request.method == "GET" and path.endswith("/pay_test"):
            return httpx.Response(200, json=self.payments[0])
        if request.method == "DELETE":
            self.payments[0]["deleted"] = True
            return httpx.Response(200, json={"deleted": True})
        if path.endswith("/refund"):
            if self.reject_refund:
                return httpx.Response(400, json={"errors": [{"code": "insufficient_balance"}]})
            self.payments[0]["status"] = "REFUNDED"
            return httpx.Response(200, json=self.payments[0])
        if path.endswith("/pixQrCode"):
            return httpx.Response(200, json={"payload": "000201-test", "expirationDate": "2026-12-31"})
        return httpx.Response(404)

    def client(self):
        return AsaasClient("test-only", transport=httpx.MockTransport(self.handle))


def issue(setup, provider, method="PIX"):
    db, tokens, patient, consultation, _ = setup
    return financial.create_charge(db, token=tokens[Role.FINANCEIRO], consultation_id=consultation.id,
            value="100.00", due_date=date.today() + timedelta(days=1), method=method, client=provider.client())


@pytest.mark.parametrize("role", [Role.RECEPCIONISTA, Role.MEDICO, Role.PACIENTE])
def test_financial_roles_denied_before_network(setup, role):
    db,tokens,_,consultation,_ = setup
    with pytest.raises(PermissionError):
        financial.create_charge(db, token=tokens[role], consultation_id=consultation.id, value="10", due_date=date.today(), method="PIX")
    assert db.exec(select(FinancialCharge)).all() == []


@pytest.mark.parametrize("method", ["PIX", "BOLETO"])
def test_issue_duplicate_and_persisted_details(setup, method):
    provider = Provider()
    charge = issue(setup, provider, method)
    db,tokens,_,consultation,_ = setup
    assert charge.status == "PENDING"
    assert consultation.status == "AGENDADA"
    assert charge.value == Decimal("100.00")
    with pytest.raises(FinancialError):
        issue(setup, provider, method)
    assert provider.calls.count(("POST", "/v3/payments")) == 1
    assert len(db.exec(select(FinancialCustomer)).all()) == 1


def test_timeout_blocks_reissue_and_reconciles_existing_external_charge(setup):
    provider = Provider()
    provider.timeout = True
    with pytest.raises(ProviderUnknown):
        issue(setup, provider)
    db,tokens,_,_,_ = setup
    charge = db.exec(select(FinancialCharge)).one()
    assert charge.status == "UNKNOWN"
    with pytest.raises(FinancialError):
        issue(setup, provider)
    financial.reconcile(db, token=tokens[Role.FINANCEIRO], charge_id=charge.id, client=provider.client())
    assert charge.status == "PENDING"
    assert provider.calls.count(("POST", "/v3/payments")) == 1


def test_received_event_idempotency_and_no_clinical_completion(setup):
    db,tokens,patient,consultation,_ = setup
    mail.set_preferences(db, token=tokens[Role.PACIENTE], patient_id=patient.id, agenda=True, financial=True, confirmed=True)
    provider = Provider()
    charge = issue(setup, provider)
    provider.payments[0]["status"] = "RECEIVED"
    db.add(FinancialWebhookEvent(event_id="evt_test", event_type="PAYMENT_RECEIVED", payment_id="pay_test"))
    db.commit()
    assert financial.process_events(db, client=provider.client()) == 1
    assert financial.process_events(db, client=provider.client()) == 0
    assert charge.status == "RECEIVED"
    assert consultation.status == "AGENDADA"
    # Late OVERDUE event reconciles the current provider state instead of regressing.
    db.add(FinancialWebhookEvent(event_id="evt_old", event_type="PAYMENT_OVERDUE", payment_id="pay_test"))
    db.commit()
    financial.process_events(db, client=provider.client())
    assert charge.status == "RECEIVED"
    assert len(db.exec(select(EmailNotification).where(EmailNotification.kind == "payment_received")).all()) == 1


def test_cancel_and_admin_only_refund(setup):
    db,tokens,_,consultation,_ = setup
    provider = Provider()
    charge = issue(setup, provider)
    financial.mutate_charge(db, token=tokens[Role.FINANCEIRO], charge_id=charge.id, operation="CANCEL", reason="Pedido do paciente", client=provider.client())
    assert charge.status == "CANCELLED" and consultation.status == "AGENDADA"
    # Refund the received record in a separate lifecycle; a provider id is never reused.
    charge.status = "PENDING"
    db.add(charge)
    db.commit()
    provider.payments[0].pop("deleted")
    provider.payments[0]["status"] = "RECEIVED"
    with pytest.raises(PermissionError):
        financial.mutate_charge(db, token=tokens[Role.FINANCEIRO], charge_id=charge.id, operation="REFUND", reason="Teste autorizado", client=provider.client())
    financial.mutate_charge(db, token=tokens[Role.ADMINISTRADOR], charge_id=charge.id, operation="REFUND", reason="Teste autorizado", client=provider.client())
    assert charge.status == "REFUNDED"


def test_outbox_unknown_no_blind_retry_and_revocation(setup, monkeypatch):
    db,tokens,patient,consultation,_ = setup
    mail.set_preferences(db, token=tokens[Role.PACIENTE], patient_id=patient.id, agenda=True, financial=False, confirmed=True)
    row = mail.enqueue_booking(db, consultation, "booking_confirmed")
    db.commit()
    calls=[]
    monkeypatch.setattr(mail.resend, "send", lambda **kw: calls.append(kw) or EmailDelivery("UNKNOWN"))
    assert mail.process_outbox(db) == 1
    assert row.status == "UNKNOWN"
    assert mail.process_outbox(db) == 0 and len(calls) == 1
    with pytest.raises(ValueError):
        mail.manual_retry(db, token=tokens[Role.RECEPCIONISTA], notification_id=row.id, reason="Revisão manual")
    mail.set_preferences(db, token=tokens[Role.PACIENTE], patient_id=patient.id, agenda=False, financial=False, confirmed=True)
    row.status = "PENDING"
    db.add(row)
    db.commit()
    assert mail.process_outbox(db) == 0
    assert row.status == "SUPPRESSED"
    assert len(db.exec(select(NotificationPreferenceChange)).all()) == 2


def test_delivery_evidence_and_html_escape(setup, monkeypatch):
    db,tokens,patient,consultation,_ = setup
    mail.set_preferences(db, token=tokens[Role.PACIENTE], patient_id=patient.id, agenda=True, financial=False, confirmed=True)
    row=mail.enqueue_booking(db,consultation,"booking_confirmed")
    db.commit()
    monkeypatch.setattr(mail.resend, "send", lambda **kw: EmailDelivery("ACCEPTED", "email_test"))
    mail.process_outbox(db)
    assert row.status == "ACCEPTED"
    db.add(EmailWebhookEvent(event_id="msg_test", event_type="email.delivered", message_id="email_test", occurred_at=datetime.now(timezone.utc)))
    db.commit()
    mail.apply_delivery_events(db)
    assert row.status == "DELIVERED"
    _,html,plain=render("booking_confirmed",name="<script>bad</script>",when="amanhã",url="https://vitta.example.test")
    assert "<script>" not in html and "&lt;script&gt;" in html
    assert "bad" in plain
    with pytest.raises(ValueError):
        render("password_reset",name="Teste")


def test_asaas_http_auth_duplicate_and_invalid_payload(setup, monkeypatch):
    db,tokens,patient,consultation,engine=setup
    monkeypatch.setenv("ASAAS_WEBHOOK_TOKEN", "x" * 40)
    @contextmanager
    def session():
        with Session(engine) as new:
            yield new
    monkeypatch.setattr("vitta_one.integration_api.rx.session",session)
    client=TestClient(Starlette(routes=provider_routes))
    event={"id":"evt_http","event":"PAYMENT_RECEIVED","payment":{"id":"pay_test"}}
    assert client.post("/api/webhooks/asaas",json=event).status_code==401
    headers={"asaas-access-token":"x"*40}
    assert client.post("/api/webhooks/asaas",json=event,headers=headers).status_code==200
    assert client.post("/api/webhooks/asaas",json=event,headers=headers).status_code==200
    assert client.post("/api/webhooks/asaas",json={},headers=headers).status_code==400
    assert len(db.exec(select(FinancialWebhookEvent)).all())==1
    assert client.post("/api/webhooks/asaas",content=b"x"*(256*1024+1),headers=headers).status_code==413


def test_resend_signed_delivery_replay_and_tampering(setup, monkeypatch):
    from svix.webhooks import Webhook
    db, tokens, patient, consultation, engine = setup
    secret = "whsec_" + base64.b64encode(b"controlled-test-signing-secret-32").decode()
    monkeypatch.setenv("RESEND_WEBHOOK_SECRET", secret)
    @contextmanager
    def session():
        with Session(engine) as new:
            yield new
    monkeypatch.setattr("vitta_one.integration_api.rx.session", session)
    client = TestClient(Starlette(routes=provider_routes))
    timestamp = datetime.now(timezone.utc)
    raw = json.dumps({"type": "email.delivered", "created_at": timestamp.isoformat(), "data": {"email_id": "email_signed"}})
    def headers(identifier, when, body):
        return {"svix-id": identifier, "svix-timestamp": str(int(when.timestamp())),
                "svix-signature": Webhook(secret).sign(identifier, when, body), "content-type": "application/json"}
    good = headers("msg_signed", timestamp, raw)
    assert client.post("/api/webhooks/resend", content=raw, headers=good).status_code == 200
    assert client.post("/api/webhooks/resend", content=raw, headers=good).status_code == 200
    assert client.post("/api/webhooks/resend", content=raw + " ", headers=good).status_code == 400
    assert client.post("/api/webhooks/resend", content=raw, headers=headers("msg_old", timestamp - timedelta(minutes=10), raw)).status_code == 400
    assert len(db.exec(select(EmailWebhookEvent)).all()) == 1
    assert client.post("/api/webhooks/resend",content=b"x"*(256*1024+1),headers=good).status_code==413


def test_reminder_window_revision_and_consent(setup, monkeypatch):
    db,tokens,patient,consultation,_=setup
    timestamp = datetime.now(timezone.utc)
    consultation.scheduled_at = timestamp + timedelta(hours=23, minutes=55)
    db.add(consultation)
    db.commit()
    mail.set_preferences(db, token=tokens[Role.PACIENTE], patient_id=patient.id, agenda=True, financial=False, confirmed=True)
    mail.enqueue_reminders(db,timestamp=timestamp)
    mail.enqueue_reminders(db,timestamp=timestamp)
    rows=db.exec(select(EmailNotification).where(EmailNotification.kind=="booking_reminder")).all()
    assert len(rows)==1
    calls=[]
    monkeypatch.setattr(mail.resend,"send",lambda **kw: calls.append(kw) or EmailDelivery("ACCEPTED","reminder_test"))
    assert mail.process_outbox(db,timestamp=timestamp+timedelta(hours=2)) == 0
    assert rows[0].status == "SUPPRESSED" and calls==[]


def test_persisted_summary_and_pagination(setup):
    from vitta_one.financial.application import snapshot, charge_detail
    db,tokens,_,consultation,_=setup
    provider=Provider()
    charge=issue(setup,provider)
    due=charge.due_date
    result=snapshot(db,token=tokens[Role.FINANCEIRO],start=due,end=due)
    assert result["total"]==1 and result["totals"]["PENDING"]=="R$ 100,00"
    provider.payments[0]["status"]="RECEIVED"
    financial.reconcile(db,token=tokens[Role.FINANCEIRO],charge_id=charge.id,client=provider.client())
    local_day=financial.now().astimezone(financial.clinic_timezone()).date()
    result=snapshot(db,token=tokens[Role.ADMINISTRADOR],start=local_day,end=due)
    assert result["totals"]["RECEIVED"]=="R$ 100,00" and result["totals"]["PENDING"]=="R$ 0,00"
    assert len(charge_detail(db,token=tokens[Role.ADMINISTRADOR],charge_id=charge.id)["history"])==2
    with pytest.raises(PermissionError):
        snapshot(db,token=tokens[Role.MEDICO],start=due,end=due)


def test_database_constraints_reject_duplicate_and_invalid_amount(setup):
    db,tokens,patient,consultation,_=setup
    charge=issue(setup,Provider())
    duplicate=FinancialCustomer(patient_id=patient.id)
    with pytest.raises(IntegrityError):
        with db.begin_nested():
            db.add(duplicate)
            db.flush()
    bad=FinancialCharge(consultation_id=consultation.id,customer_id=charge.customer_id,created_by=charge.created_by,
                        value=Decimal('-1'),method='PIX',due_date=charge.due_date,status='REFUNDED')
    with pytest.raises(IntegrityError):
        with db.begin_nested():
            db.add(bad)
            db.flush()
    invalid_fk=FinancialCharge(consultation_id=9999999,customer_id=charge.customer_id,created_by=charge.created_by,
                        value=Decimal('10'),method='PIX',due_date=charge.due_date,status='REFUNDED')
    with pytest.raises(IntegrityError):
        with db.begin_nested():
            db.add(invalid_fk)
            db.flush()
    assert db.exec(select(FinancialCharge)).one().id==charge.id


def test_postgres_concurrent_emission_has_one_external_effect(setup):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    db,tokens,patient,consultation,engine=setup
    if engine.dialect.name!='postgresql':
        pytest.skip('Row-locking concurrency requires PostgreSQL.')
    barrier=Barrier(2)
    consultation_id=consultation.id
    token=tokens[Role.FINANCEIRO]
    provider=Provider()
    def emit():
        with Session(engine) as worker_db:
            barrier.wait(timeout=10)
            try:
                return financial.create_charge(worker_db,token=token,consultation_id=consultation_id,
                        value='100.00',due_date=date.today()+timedelta(days=1),method='PIX',client=provider.client()).id
            except FinancialError:
                worker_db.rollback()
                return None
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda _:emit(),range(2)))
    assert sum(result is not None for result in results)==1
    assert provider.calls.count(('POST','/v3/payments'))==1


def test_invalid_and_provisional_session_denied(setup):
    db,tokens,patient,consultation,_=setup
    with pytest.raises(PermissionError):
        financial.authorize(db,'')
    expired=create_session(db,user_id=db.exec(select(User.id).where(User.role==Role.FINANCEIRO.value)).one(),
                           ttl=timedelta(seconds=1),now=datetime.now(timezone.utc)-timedelta(hours=1))
    with pytest.raises(PermissionError):
        financial.authorize(db,expired)
    user=db.exec(select(User).where(User.role==Role.FINANCEIRO.value)).one()
    user.must_change_password=True
    db.add(user)
    db.commit()
    with pytest.raises(PermissionError):
        financial.authorize(db,tokens[Role.FINANCEIRO])


def test_existing_external_cpf_blocks_duplicate_customer(setup):
    provider=Provider()
    provider.customers=[{'id':'cus_existing','cpfCnpj':'52998224725','externalReference':'other-system'}]
    with pytest.raises(FinancialError):
        issue(setup,provider)
    assert not any(method=='POST' for method,path in provider.calls)


def test_customer_update_and_refund_rejection_preserve_state(setup):
    from vitta_one.financial.asaas import ProviderRejected
    db,tokens,patient,consultation,_=setup
    provider=Provider()
    charge=issue(setup,provider)
    patient.name='Paciente Atualizado'
    db.add(patient)
    db.commit()
    customer=financial.sync_customer(db,token=tokens[Role.FINANCEIRO],patient_id=patient.id,client=provider.client())
    assert customer.provider_id=='cus_test' and provider.customers[0]['name']=='Paciente Atualizado'
    provider.payments[0]['status']='RECEIVED'
    provider.reject_refund=True
    with pytest.raises(ProviderRejected):
        financial.mutate_charge(db,token=tokens[Role.ADMINISTRADOR],charge_id=charge.id,operation='REFUND',reason='Revisão autorizada',client=provider.client())
    assert charge.status=='RECEIVED' and charge.operation==''


def test_financial_rollback_has_no_payment_notification(setup):
    db,tokens,patient,consultation,_=setup
    mail.set_preferences(db,token=tokens[Role.PACIENTE],patient_id=patient.id,agenda=False,financial=True,confirmed=True)
    provider=Provider()
    charge=issue(setup,provider)
    provider.payments[0]['status']='RECEIVED'
    financial._apply_snapshot(db,charge.id,provider.payments[0],expected_revision=charge.revision,source='TEST')
    db.rollback()
    db.refresh(charge)
    assert charge.status=='PENDING'
    assert db.exec(select(EmailNotification).where(EmailNotification.kind=='payment_received')).all()==[]


def test_booking_service_hooks_commit_notifications_once(setup):
    from vitta_one.appointment_scheduling.service import schedule_consultation,reschedule_consultation,cancel_consultation
    db,tokens,patient,existing,_=setup
    mail.set_preferences(db,token=tokens[Role.PACIENTE],patient_id=patient.id,agenda=True,financial=False,confirmed=True)
    slots=[]
    for days in (4,5):
        slot=ProfessionalAvailabilitySlot(professional_id=existing.professional_id,starts_at=datetime.now(timezone.utc)+timedelta(days=days))
        db.add(slot)
        db.flush()
        slots.append(slot)
    db.commit()
    consultation=schedule_consultation(db,patient_id=patient.id,slot_id=slots[0].id)
    reschedule_consultation(db,consultation_id=consultation.id,new_slot_id=slots[1].id)
    cancel_consultation(db,consultation_id=consultation.id)
    assert {n.kind for n in db.exec(select(EmailNotification)).all()}=={'booking_confirmed','booking_rescheduled','booking_cancelled'}


def test_tracked_medical_access_never_persists_secret_or_repeats(setup,monkeypatch):
    from vitta_one.professional_directory import email_sender
    db,tokens,patient,consultation,engine=setup
    professional=db.get(Professional,consultation.professional_id)
    user=db.exec(select(User).where(User.role==Role.MEDICO.value)).one()
    user.must_change_password=True
    user.temporary_password_expires_at=datetime.now(timezone.utc)+timedelta(hours=24)
    professional.user_id=user.id
    db.add(user)
    db.add(professional)
    db.commit()
    @contextmanager
    def session():
        with Session(engine) as new:
            yield new
    import reflex as rx
    monkeypatch.setattr(rx,'session',session)
    calls=[]
    monkeypatch.setattr(email_sender,'_medical_content',lambda **kw:calls.append(kw) or EmailDelivery('ACCEPTED','medical_test'))
    args=dict(name=professional.name,email=user.email,temporary_password='transient-secret-test-only',professional_id=professional.id,token=tokens[Role.ADMINISTRADOR])
    assert email_sender.send_medical_welcome(**args).status=='ACCEPTED'
    assert email_sender.send_medical_welcome(**args).status=='ACCEPTED'
    assert len(calls)==1
    record=db.exec(select(EmailNotification).where(EmailNotification.kind=='medical_access')).one()
    assert 'transient-secret-test-only' not in str(record.model_dump())
