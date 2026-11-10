"""Financial domain coverage for exact totals, portal scope and idempotent webhooks."""

from datetime import date

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from vitta_one.auth.roles import Role
from vitta_one.finance.service import (
    AccountItemInput, FinanceAuthorizationError, create_service, dashboard,
    issue_account, list_patient_accounts, process_asaas_webhook, reconcile_charge,
)
from vitta_one.integrations.asaas import AsaasCharge
from vitta_one.models.auth import User
from vitta_one.models.finance import BillingCharge, PatientAccount, PaymentRecord
from vitta_one.models.patient_queue import Patient


@pytest.fixture
def db() -> Session:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def _context(db: Session):
    finance = User(email="finance@example.com", password_hash="hash", role=Role.FINANCEIRO.value)
    patient_user = User(email="patient-finance@example.com", password_hash="hash", role=Role.PACIENTE.value)
    db.add(finance)
    db.add(patient_user)
    db.flush()
    patient = Patient(name="Paciente Financeiro", cpf="12345678901", user_id=patient_user.id)
    db.add(patient)
    db.commit()
    for row in (finance, patient_user, patient):
        db.refresh(row)
    return finance, patient_user, patient


def test_account_totals_and_patient_scope_are_server_side(db: Session) -> None:
    finance, patient_user, patient = _context(db)
    service = create_service(db, actor_user_id=finance.id, name="Consulta", description="", unit_price_cents=12345)
    account = issue_account(
        db, actor_user_id=finance.id, patient_id=patient.id,
        due_date=date(2026, 12, 1), items=[AccountItemInput(service.id, 2)],
    )
    assert account.total_cents == 24690
    assert list_patient_accounts(db, patient_user_id=patient_user.id)[0].id == account.id
    assert dashboard(db, today=date(2026, 11, 10)).open_cents == 24690

    outsider = User(email="outsider@example.com", password_hash="hash", role=Role.PACIENTE.value)
    db.add(outsider)
    db.commit()
    with pytest.raises(FinanceAuthorizationError):
        list_patient_accounts(db, patient_user_id=outsider.id)


def test_asaas_webhook_is_idempotent_and_does_not_double_payment(db: Session) -> None:
    finance, _, patient = _context(db)
    service = create_service(db, actor_user_id=finance.id, name="Exame", description="", unit_price_cents=5000)
    account_view = issue_account(
        db, actor_user_id=finance.id, patient_id=patient.id,
        due_date=date(2026, 12, 1), items=[AccountItemInput(service.id, 1)],
    )
    charge = BillingCharge(
        account_id=account_view.id, request_key="r" * 64, external_reference="vitta-account-test",
        provider_charge_id="pay_test", billing_type="PIX", status="PENDING",
        due_date=date(2026, 12, 1), value_cents=5000,
    )
    db.add(charge)
    db.commit()
    payload = {
        "id": "evt_test", "event": "PAYMENT_RECEIVED",
        "payment": {"id": "pay_test", "status": "RECEIVED", "value": 50.00},
    }

    assert process_asaas_webhook(db, payload) == "PROCESSED"
    assert process_asaas_webhook(db, payload) == "DUPLICATE"
    assert len(db.exec(select(PaymentRecord)).all()) == 1
    account = db.get(PatientAccount, account_view.id)
    assert account.paid_cents == 5000
    assert account.status == "PAID"


def test_uncertain_charge_is_reconciled_without_creating_another_payment(db: Session) -> None:
    finance, _, patient = _context(db)
    service = create_service(db, actor_user_id=finance.id, name="Consulta retorno", description="", unit_price_cents=9000)
    account = issue_account(
        db, actor_user_id=finance.id, patient_id=patient.id,
        due_date=date(2026, 12, 1), items=[AccountItemInput(service.id, 1)],
    )
    charge = BillingCharge(
        account_id=account.id, request_key="x" * 64,
        external_reference=f"vitta-account-{account.id}", billing_type="PIX",
        status="RECONCILIATION_REQUIRED", status_detail_code="CREATE_RESULT_UNKNOWN",
        due_date=date(2026, 12, 1), value_cents=9000,
    )
    db.add(charge)
    db.commit()
    db.refresh(charge)

    class _Client:
        def find_charge(self, external_reference: str):
            assert external_reference == f"vitta-account-{account.id}"
            return AsaasCharge("pay-reconciled", "PENDING", "https://sandbox.example/invoice")

    result = reconcile_charge(
        db, actor_user_id=finance.id, charge_id=charge.id, client=_Client()
    )

    assert result.charge_status == "PENDING"
    refreshed = db.get(BillingCharge, charge.id)
    assert refreshed.provider_charge_id == "pay-reconciled"
    assert refreshed.status_detail_code == ""
