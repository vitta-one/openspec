"""Persistent patient and reception queue models."""

from datetime import datetime, timezone

import reflex as rx
from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, String, Text
from sqlmodel import Field

from vitta_one.patient_queue.domain import QueuePriority, QueueStatus


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


class Patient(rx.Model, table=True):
    """Minimal reusable patient identity required by the queue flow."""

    __tablename__ = "patients"

    name: str = Field(sa_column=Column(String(160), nullable=False))
    cpf: str = Field(
        sa_column=Column(String(11), nullable=False, unique=True, index=True)
    )
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class QueueEntry(rx.Model, table=True):
    """One patient passage through the operational reception queue."""

    __tablename__ = "queue_entries"
    __table_args__ = (
        CheckConstraint(
            "priority IN ('VERMELHO', 'AMARELO', 'VERDE')",
            name="ck_queue_entries_priority",
        ),
        CheckConstraint(
            "status IN ('AGUARDANDO', 'EM_ATENDIMENTO', 'FINALIZADO', 'RETIRADO')",
            name="ck_queue_entries_status",
        ),
    )

    patient_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("patients.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        )
    )
    symptoms: str = Field(sa_column=Column(Text, nullable=False))
    priority: str = Field(sa_column=Column(String(16), nullable=False, index=True))
    status: str = Field(sa_column=Column(String(20), nullable=False, index=True))
    entered_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    doctor_user_id: int | None = Field(
        default=None,
        sa_column=Column(
            Integer,
            ForeignKey("auth_users.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
    )
    called_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    finished_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    withdrawn_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    withdrawal_reason: str | None = Field(
        default=None,
        sa_column=Column(String(300), nullable=True),
    )

    @property
    def parsed_priority(self) -> QueuePriority:
        return QueuePriority(self.priority)

    @property
    def parsed_status(self) -> QueueStatus:
        return QueueStatus(self.status)
