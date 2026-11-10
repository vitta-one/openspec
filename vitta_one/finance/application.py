"""Authenticated application boundary for financial operations."""

from datetime import date

from sqlmodel import Session

from vitta_one.auth.authorization import require_role
from vitta_one.auth.roles import Role
from .service import (
    AccountItemInput, AccountView, DashboardView, ServiceView, cancel_charge, create_charge,
    create_service, dashboard, issue_account, list_accounts, list_patient_accounts,
    reconcile_charge,
    list_services, set_service_active,
)


def finance_create_service(db: Session, *, token: str, name: str, description: str, unit_price_cents: int) -> ServiceView:
    identity = require_role(db, token, Role.FINANCEIRO)
    return create_service(db, actor_user_id=identity.id, name=name, description=description, unit_price_cents=unit_price_cents)


def finance_set_service_active(db: Session, *, token: str, service_id: int, active: bool) -> ServiceView:
    identity = require_role(db, token, Role.FINANCEIRO)
    return set_service_active(db, actor_user_id=identity.id, service_id=service_id, active=active)


def finance_list_services(db: Session, *, token: str, include_inactive: bool = False) -> tuple[ServiceView, ...]:
    require_role(db, token, Role.FINANCEIRO)
    return list_services(db, include_inactive=include_inactive)


def finance_issue_account(
    db: Session,
    *,
    token: str,
    patient_id: int,
    due_date: date,
    items: list[AccountItemInput],
    consultation_id: int | None = None,
) -> AccountView:
    identity = require_role(db, token, Role.FINANCEIRO)
    return issue_account(
        db,
        actor_user_id=identity.id,
        patient_id=patient_id,
        due_date=due_date,
        items=items,
        consultation_id=consultation_id,
    )


def finance_create_charge(db: Session, *, token: str, account_id: int, billing_type: str, client=None) -> AccountView:
    identity = require_role(db, token, Role.FINANCEIRO)
    return create_charge(db, actor_user_id=identity.id, account_id=account_id, billing_type=billing_type, client=client)


def finance_cancel_charge(db: Session, *, token: str, charge_id: int, client=None) -> None:
    identity = require_role(db, token, Role.FINANCEIRO)
    cancel_charge(db, actor_user_id=identity.id, charge_id=charge_id, client=client)


def finance_reconcile_charge(db: Session, *, token: str, charge_id: int, client=None) -> AccountView:
    identity = require_role(db, token, Role.FINANCEIRO)
    return reconcile_charge(
        db,
        actor_user_id=identity.id,
        charge_id=charge_id,
        client=client,
    )


def finance_list_accounts(db: Session, *, token: str) -> tuple[AccountView, ...]:
    require_role(db, token, Role.FINANCEIRO)
    return list_accounts(db)


def finance_dashboard(db: Session, *, token: str) -> DashboardView:
    require_role(db, token, Role.FINANCEIRO)
    return dashboard(db)


def patient_financial_accounts(db: Session, *, token: str) -> tuple[AccountView, ...]:
    identity = require_role(db, token, Role.PACIENTE)
    return list_patient_accounts(db, patient_user_id=identity.id)
