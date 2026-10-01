"""Persistent availability-slot and consultation models."""

from datetime import datetime, timezone

import reflex as rx
from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, text
from sqlmodel import Field

from vitta_one.appointment_scheduling.domain import AvailabilitySlotStatus, ConsultationStatus


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ProfessionalAvailabilitySlot(rx.Model, table=True):
    """One explicit reservable instant for one professional."""

    __tablename__ = "professional_availability_slots"
    __table_args__ = (
        UniqueConstraint(
            "professional_id",
            "starts_at",
            name="uq_availability_professional_starts_at",
        ),
        CheckConstraint(
            "status IN ('AVAILABLE', 'BOOKED', 'INACTIVE')",
            name="ck_availability_slot_status",
        ),
        Index("ix_availability_professional_starts_at", "professional_id", "starts_at"),
    )

    professional_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("professionals.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        )
    )
    starts_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True)
    )
    status: str = Field(
        default=AvailabilitySlotStatus.AVAILABLE.value,
        sa_column=Column(String(16), nullable=False, index=True),
    )
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class Consultation(rx.Model, table=True):
    """A scheduled clinical commitment backed by one availability slot."""

    __tablename__ = "consultations"
    __table_args__ = (
        CheckConstraint(
            "status IN ('AGENDADA', 'CONFIRMADA', 'EM_ANDAMENTO', 'CONCLUIDA', 'CANCELADA')",
            name="ck_consultations_status",
        ),
        Index("ix_consultations_professional_scheduled", "professional_id", "scheduled_at"),
        Index("ix_consultations_status_scheduled", "status", "scheduled_at"),
        Index(
            "uq_consultations_active_slot",
            "availability_slot_id",
            unique=True,
            postgresql_where=text("status <> 'CANCELADA'"),
            sqlite_where=text("status <> 'CANCELADA'"),
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
    professional_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("professionals.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        )
    )
    availability_slot_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("professional_availability_slots.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        )
    )
    scheduled_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True)
    )
    status: str = Field(
        default=ConsultationStatus.AGENDADA.value,
        sa_column=Column(String(20), nullable=False, index=True),
    )
    confirmed_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    started_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    completed_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    cancelled_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
