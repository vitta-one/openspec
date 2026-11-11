"""Notification metadata only: message bodies and access secrets are never stored."""
from datetime import datetime
from uuid import uuid4

import reflex as rx
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlmodel import Field

from .financial import fk, now


class NotificationPreference(rx.Model, table=True):
    __tablename__ = "notification_preferences"
    patient_id: int = Field(sa_column=fk("patients", unique=True))
    agenda_enabled: bool = Field(default=False, sa_column=Column(Boolean, nullable=False))
    financial_enabled: bool = Field(default=False, sa_column=Column(Boolean, nullable=False))
    changed_by: int = Field(sa_column=fk("auth_users"))
    changed_at: datetime = Field(default_factory=now, sa_column=Column(DateTime(timezone=True), nullable=False))


class NotificationPreferenceChange(rx.Model, table=True):
    __tablename__ = "notification_preference_changes"
    patient_id: int = Field(sa_column=fk("patients"))
    changed_by: int = Field(sa_column=fk("auth_users"))
    agenda_enabled: bool = Field(default=False)
    financial_enabled: bool = Field(default=False)
    occurred_at: datetime = Field(default_factory=now, sa_column=Column(DateTime(timezone=True), nullable=False))


class EmailNotification(rx.Model, table=True):
    __tablename__ = "email_notifications"
    __table_args__ = (UniqueConstraint("event_key", "recipient_hash", name="uq_email_event_recipient"),)
    kind: str = Field(sa_column=Column(String(48), nullable=False))
    event_key: str = Field(sa_column=Column(String(180), nullable=False))
    recipient_hash: str = Field(sa_column=Column(String(64), nullable=False))
    # A local reference is resolved on the server; this is not arbitrary message content.
    entity_id: int = Field()
    revision: str = Field(default="", sa_column=Column(String(100), nullable=False))
    patient_id: int | None = Field(default=None, sa_column=Column(Integer, ForeignKey("patients.id", ondelete="RESTRICT")))
    status: str = Field(default="PENDING", sa_column=Column(String(24), nullable=False, index=True))
    error_code: str = Field(default="", sa_column=Column(String(48), nullable=False))
    created_at: datetime = Field(default_factory=now, sa_column=Column(DateTime(timezone=True), nullable=False))
    updated_at: datetime = Field(default_factory=now, sa_column=Column(DateTime(timezone=True), nullable=False))


class EmailAttempt(rx.Model, table=True):
    __tablename__ = "email_attempts"
    __table_args__ = (UniqueConstraint("notification_id", "sequence", name="uq_email_attempt_sequence"),)
    notification_id: int = Field(sa_column=fk("email_notifications"))
    sequence: int = Field(default=1)
    idempotency_key: str = Field(default_factory=lambda: "vitta/" + uuid4().hex, sa_column=Column(String(80), nullable=False, unique=True))
    provider: str = Field(default="resend", sa_column=Column(String(24), nullable=False))
    message_id: str | None = Field(default=None, sa_column=Column(String(128), unique=True))
    status: str = Field(default="SENDING", sa_column=Column(String(24), nullable=False))
    error_code: str = Field(default="", sa_column=Column(String(48), nullable=False))
    started_at: datetime = Field(default_factory=now, sa_column=Column(DateTime(timezone=True), nullable=False))
    finished_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True)))


class EmailWebhookEvent(rx.Model, table=True):
    __tablename__ = "email_webhook_events"
    event_id: str = Field(sa_column=Column(String(180), nullable=False, unique=True))
    event_type: str = Field(sa_column=Column(String(64), nullable=False))
    message_id: str = Field(sa_column=Column(String(128), nullable=False, index=True))
    status: str = Field(default="PENDING", sa_column=Column(String(24), nullable=False))
    occurred_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    received_at: datetime = Field(default_factory=now, sa_column=Column(DateTime(timezone=True), nullable=False))


class EmailRetryRequest(rx.Model, table=True):
    __tablename__ = "email_retry_requests"
    notification_id: int = Field(sa_column=fk("email_notifications"))
    requested_by: int = Field(sa_column=fk("auth_users"))
    reason: str = Field(sa_column=Column(String(240), nullable=False))
    uncertainty_reviewed: bool = Field(default=False)
    requested_at: datetime = Field(default_factory=now, sa_column=Column(DateTime(timezone=True), nullable=False))
