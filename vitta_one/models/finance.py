"""Financial catalog, accounts, billing and reconciliation models."""

from datetime import date, datetime, timezone

import reflex as rx
from sqlalchemy import Boolean, CheckConstraint, Column, Date, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlmodel import Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class FinancialService(rx.Model, table=True):
    __tablename__ = "financial_services"
    __table_args__ = (CheckConstraint("unit_price_cents > 0", name="ck_financial_services_price"),)

    name: str = Field(sa_column=Column(String(160), nullable=False, unique=True, index=True))
    description: str = Field(default="", sa_column=Column(Text, nullable=False))
    unit_price_cents: int = Field(sa_column=Column(Integer, nullable=False))
    active: bool = Field(default=True, sa_column=Column(Boolean, nullable=False, index=True))
    created_by_user_id: int = Field(sa_column=Column(Integer, ForeignKey("auth_users.id", ondelete="RESTRICT"), nullable=False))
    updated_by_user_id: int = Field(sa_column=Column(Integer, ForeignKey("auth_users.id", ondelete="RESTRICT"), nullable=False))
    created_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), nullable=False))
    updated_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), nullable=False))


class PatientAccount(rx.Model, table=True):
    __tablename__ = "patient_accounts"
    __table_args__ = (
        CheckConstraint("total_cents >= 0", name="ck_patient_accounts_total"),
        CheckConstraint("paid_cents >= 0 AND paid_cents <= total_cents", name="ck_patient_accounts_paid"),
        CheckConstraint(
            "status IN ('OPEN', 'PARTIALLY_PAID', 'PAID', 'CANCELLED')",
            name="ck_patient_accounts_status",
        ),
        Index("ix_patient_accounts_patient_created", "patient_id", "created_at"),
    )

    patient_id: int = Field(sa_column=Column(Integer, ForeignKey("patients.id", ondelete="RESTRICT"), nullable=False, index=True))
    consultation_id: int | None = Field(
        default=None,
        sa_column=Column(
            Integer,
            ForeignKey("consultations.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
    )
    issued_by_user_id: int = Field(sa_column=Column(Integer, ForeignKey("auth_users.id", ondelete="RESTRICT"), nullable=False, index=True))
    status: str = Field(default="OPEN", sa_column=Column(String(24), nullable=False, index=True))
    due_date: date = Field(sa_column=Column(Date, nullable=False, index=True))
    total_cents: int = Field(default=0, sa_column=Column(Integer, nullable=False))
    paid_cents: int = Field(default=0, sa_column=Column(Integer, nullable=False))
    created_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), nullable=False, index=True))
    updated_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), nullable=False))
    cancelled_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))


class PatientAccountItem(rx.Model, table=True):
    __tablename__ = "patient_account_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_patient_account_items_quantity"),
        CheckConstraint("unit_price_cents > 0", name="ck_patient_account_items_unit_price"),
        CheckConstraint("total_cents = quantity * unit_price_cents", name="ck_patient_account_items_total"),
        Index("ix_patient_account_items_account", "account_id", "id"),
    )

    account_id: int = Field(sa_column=Column(Integer, ForeignKey("patient_accounts.id", ondelete="CASCADE"), nullable=False, index=True))
    service_id: int | None = Field(default=None, sa_column=Column(Integer, ForeignKey("financial_services.id", ondelete="SET NULL"), nullable=True))
    description_snapshot: str = Field(sa_column=Column(String(300), nullable=False))
    quantity: int = Field(sa_column=Column(Integer, nullable=False))
    unit_price_cents: int = Field(sa_column=Column(Integer, nullable=False))
    total_cents: int = Field(sa_column=Column(Integer, nullable=False))


class BillingCustomer(rx.Model, table=True):
    __tablename__ = "billing_customers"

    patient_id: int = Field(sa_column=Column(Integer, ForeignKey("patients.id", ondelete="RESTRICT"), nullable=False, unique=True, index=True))
    provider_customer_id: str = Field(sa_column=Column(String(80), nullable=False, unique=True, index=True))
    created_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), nullable=False))
    updated_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), nullable=False))


class BillingCharge(rx.Model, table=True):
    __tablename__ = "billing_charges"
    __table_args__ = (
        CheckConstraint("value_cents > 0", name="ck_billing_charges_value"),
        CheckConstraint(
            "billing_type IN ('UNDEFINED', 'BOLETO', 'PIX', 'CREDIT_CARD')",
            name="ck_billing_charges_type",
        ),
        CheckConstraint(
            "status IN ('CREATING', 'PENDING', 'RECEIVED', 'CONFIRMED', 'OVERDUE', "
            "'CANCELLED', 'REFUNDED', 'RECONCILIATION_REQUIRED', 'FAILED')",
            name="ck_billing_charges_status",
        ),
        Index("ix_billing_charges_account_created", "account_id", "created_at"),
    )

    account_id: int = Field(sa_column=Column(Integer, ForeignKey("patient_accounts.id", ondelete="RESTRICT"), nullable=False, index=True))
    request_key: str = Field(sa_column=Column(String(64), nullable=False, unique=True, index=True))
    external_reference: str = Field(sa_column=Column(String(80), nullable=False, unique=True, index=True))
    provider_charge_id: str | None = Field(default=None, sa_column=Column(String(80), nullable=True, unique=True, index=True))
    billing_type: str = Field(sa_column=Column(String(20), nullable=False))
    status: str = Field(default="CREATING", sa_column=Column(String(32), nullable=False, index=True))
    due_date: date = Field(sa_column=Column(Date, nullable=False, index=True))
    value_cents: int = Field(sa_column=Column(Integer, nullable=False))
    invoice_url: str | None = Field(default=None, sa_column=Column(String(1000), nullable=True))
    status_detail_code: str = Field(default="", sa_column=Column(String(80), nullable=False))
    created_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), nullable=False, index=True))
    updated_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), nullable=False))
    last_provider_sync_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))


class PaymentRecord(rx.Model, table=True):
    __tablename__ = "payment_records"
    __table_args__ = (
        CheckConstraint("amount_cents > 0", name="ck_payment_records_amount"),
        CheckConstraint(
            "status IN ('RECEIVED', 'CONFIRMED', 'REFUNDED', 'CHARGEBACK')",
            name="ck_payment_records_status",
        ),
        UniqueConstraint("provider_payment_id", name="uq_payment_provider_payment_id"),
    )

    charge_id: int = Field(sa_column=Column(Integer, ForeignKey("billing_charges.id", ondelete="RESTRICT"), nullable=False, index=True))
    provider_payment_id: str = Field(sa_column=Column(String(80), nullable=False, index=True))
    provider_event_id: str = Field(sa_column=Column(String(160), nullable=False, index=True))
    amount_cents: int = Field(sa_column=Column(Integer, nullable=False))
    status: str = Field(sa_column=Column(String(24), nullable=False, index=True))
    paid_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    created_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), nullable=False, index=True))


class BillingWebhookEvent(rx.Model, table=True):
    __tablename__ = "billing_webhook_events"

    event_id: str = Field(sa_column=Column(String(160), nullable=False, unique=True, index=True))
    event_type: str = Field(sa_column=Column(String(80), nullable=False, index=True))
    provider_charge_id: str | None = Field(default=None, sa_column=Column(String(80), nullable=True, index=True))
    received_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), nullable=False, index=True))
    processed_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    outcome: str = Field(default="RECEIVED", sa_column=Column(String(32), nullable=False))


class FinancialAudit(rx.Model, table=True):
    __tablename__ = "financial_audits"
    __table_args__ = (Index("ix_financial_audits_resource_created", "resource_type", "resource_id", "created_at"),)

    resource_type: str = Field(sa_column=Column(String(40), nullable=False))
    resource_id: int = Field(sa_column=Column(Integer, nullable=False))
    actor_user_id: int | None = Field(default=None, sa_column=Column(Integer, ForeignKey("auth_users.id", ondelete="SET NULL"), nullable=True, index=True))
    action: str = Field(sa_column=Column(String(40), nullable=False))
    outcome: str = Field(sa_column=Column(String(24), nullable=False))
    detail_code: str = Field(default="", sa_column=Column(String(80), nullable=False))
    created_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), nullable=False, index=True))
