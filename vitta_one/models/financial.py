"""Minimal financial records, separate from clinical state and personal data."""
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

import reflex as rx
from sqlalchemy import CheckConstraint, Column, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, text
from sqlmodel import Field


def now() -> datetime:
    return datetime.now(timezone.utc)


def fk(table: str, *, unique=False):
    return Column(Integer, ForeignKey(f"{table}.id", ondelete="RESTRICT"), nullable=False, unique=unique, index=True)


class FinancialCustomer(rx.Model, table=True):
    __tablename__ = "financial_customers"
    patient_id: int = Field(sa_column=fk("patients", unique=True))
    reference: str = Field(default_factory=lambda: "vitta-patient-" + uuid4().hex, sa_column=Column(String(80), nullable=False, unique=True))
    provider_id: str | None = Field(default=None, sa_column=Column(String(128), unique=True))
    status: str = Field(default="NEW", sa_column=Column(String(24), nullable=False))
    updated_at: datetime = Field(default_factory=now, sa_column=Column(DateTime(timezone=True), nullable=False))


class FinancialCharge(rx.Model, table=True):
    __tablename__ = "financial_charges"
    __table_args__ = (
        CheckConstraint("value > 0", name="ck_financial_charge_positive"),
        CheckConstraint("method IN ('PIX', 'BOLETO')", name="ck_financial_charge_method"),
        Index("uq_financial_charge_active_consultation", "consultation_id", unique=True,
              postgresql_where=text("status NOT IN ('CANCELLED','REFUNDED')"),
              sqlite_where=text("status NOT IN ('CANCELLED','REFUNDED')")),
    )
    consultation_id: int = Field(sa_column=fk("consultations"))
    customer_id: int = Field(sa_column=fk("financial_customers"))
    created_by: int = Field(sa_column=fk("auth_users"))
    reference: str = Field(default_factory=lambda: "vitta-charge-" + uuid4().hex, sa_column=Column(String(80), nullable=False, unique=True))
    provider_id: str | None = Field(default=None, sa_column=Column(String(128), unique=True))
    value: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
    method: str = Field(sa_column=Column(String(16), nullable=False))
    due_date: date = Field(sa_column=Column(Date, nullable=False, index=True))
    status: str = Field(default="NEW", sa_column=Column(String(24), nullable=False, index=True))
    provider_status: str = Field(default="", sa_column=Column(String(48), nullable=False))
    operation: str = Field(default="", sa_column=Column(String(24), nullable=False))
    revision: int = Field(default=0)
    invoice_url: str = Field(default="", sa_column=Column(String(2048), nullable=False))
    boleto_url: str = Field(default="", sa_column=Column(String(2048), nullable=False))
    created_at: datetime = Field(default_factory=now, sa_column=Column(DateTime(timezone=True), nullable=False))
    updated_at: datetime = Field(default_factory=now, sa_column=Column(DateTime(timezone=True), nullable=False))
    received_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))


class FinancialChange(rx.Model, table=True):
    __tablename__ = "financial_changes"
    charge_id: int = Field(sa_column=fk("financial_charges"))
    event_key: str = Field(sa_column=Column(String(180), nullable=False, unique=True))
    previous_status: str = Field(sa_column=Column(String(24), nullable=False))
    status: str = Field(sa_column=Column(String(24), nullable=False))
    source: str = Field(sa_column=Column(String(32), nullable=False))
    actor_id: int | None = Field(default=None, sa_column=Column(Integer, ForeignKey("auth_users.id", ondelete="RESTRICT")))
    reason: str = Field(default="", sa_column=Column(String(240), nullable=False))
    occurred_at: datetime = Field(default_factory=now, sa_column=Column(DateTime(timezone=True), nullable=False))


class FinancialWebhookEvent(rx.Model, table=True):
    __tablename__ = "financial_webhook_events"
    event_id: str = Field(sa_column=Column(String(180), nullable=False, unique=True))
    event_type: str = Field(sa_column=Column(String(80), nullable=False))
    payment_id: str = Field(sa_column=Column(String(128), nullable=False, index=True))
    status: str = Field(default="PENDING", sa_column=Column(String(24), nullable=False, index=True))
    attempts: int = Field(default=0)
    lease_until: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    next_attempt_at: datetime = Field(default_factory=now, sa_column=Column(DateTime(timezone=True), nullable=False))
    error_code: str = Field(default="", sa_column=Column(String(48), nullable=False))
    received_at: datetime = Field(default_factory=now, sa_column=Column(DateTime(timezone=True), nullable=False))
