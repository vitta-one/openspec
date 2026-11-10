"""Persisted state for prescription signature orchestration."""

from datetime import datetime, timezone

import reflex as rx
from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, String
from sqlmodel import Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


_SIGNATURE_STATES = (
    "CREATING", "PENDING", "SIGNED", "REFUSED", "EXPIRED", "CANCELLED",
    "RECONCILIATION_REQUIRED", "FAILED",
)


class PrescriptionSignatureRequest(rx.Model, table=True):
    """One idempotent provider document for a prescription."""

    __tablename__ = "prescription_signature_requests"
    __table_args__ = (
        CheckConstraint(
            "status IN ('CREATING', 'PENDING', 'SIGNED', 'REFUSED', 'EXPIRED', "
            "'CANCELLED', 'RECONCILIATION_REQUIRED', 'FAILED')",
            name="ck_prescription_signature_requests_status",
        ),
        Index("ix_prescription_signature_status_updated", "status", "updated_at"),
    )

    prescription_id: int = Field(
        sa_column=Column(Integer, ForeignKey("prescriptions.id", ondelete="RESTRICT"), nullable=False, unique=True, index=True)
    )
    requested_by_user_id: int = Field(
        sa_column=Column(Integer, ForeignKey("auth_users.id", ondelete="RESTRICT"), nullable=False, index=True)
    )
    request_key: str = Field(sa_column=Column(String(64), nullable=False, unique=True, index=True))
    external_id: str = Field(sa_column=Column(String(80), nullable=False, unique=True, index=True))
    provider_document_token: str | None = Field(default=None, sa_column=Column(String(128), nullable=True, unique=True, index=True))
    provider_signer_token: str | None = Field(default=None, sa_column=Column(String(128), nullable=True))
    signer_email: str = Field(sa_column=Column(String(320), nullable=False))
    status: str = Field(default="CREATING", sa_column=Column(String(32), nullable=False, index=True))
    status_detail_code: str = Field(default="", sa_column=Column(String(80), nullable=False))
    created_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), nullable=False, index=True))
    updated_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), nullable=False))
    last_provider_sync_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    signed_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))


class SignatureWebhookEvent(rx.Model, table=True):
    """Deduplication record for at-least-once provider deliveries."""

    __tablename__ = "signature_webhook_events"

    event_id: str = Field(sa_column=Column(String(160), nullable=False, unique=True, index=True))
    event_type: str = Field(sa_column=Column(String(64), nullable=False, index=True))
    provider_document_token: str | None = Field(default=None, sa_column=Column(String(128), nullable=True, index=True))
    received_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), nullable=False, index=True))
    processed_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    outcome: str = Field(default="RECEIVED", sa_column=Column(String(32), nullable=False))

