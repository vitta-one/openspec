"""Clinical care record attached to a scheduled consultation OR walk-in queue entry."""

from datetime import datetime, timezone

import reflex as rx
from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Index, Integer, Text, UniqueConstraint
from sqlmodel import Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ClinicalCareRecord(rx.Model, table=True):
    """Basic clinical content authored by the responsible doctor during care."""

    __tablename__ = "clinical_care_records"
    __table_args__ = (
        UniqueConstraint(
            "consultation_id",
            name="uq_clinical_care_records_consultation_id",
        ),
        UniqueConstraint("queue_entry_id", name="uq_clinical_care_records_queue_entry_id"),
        CheckConstraint(
            "(consultation_id IS NOT NULL AND queue_entry_id IS NULL) OR "
            "(consultation_id IS NULL AND queue_entry_id IS NOT NULL)",
            name="ck_clinical_care_records_one_episode",
        ),
        Index(
            "ix_clinical_care_records_patient_updated",
            "patient_id",
            "updated_at",
        ),
    )

    consultation_id: int | None = Field(
        default=None,
        sa_column=Column(
            Integer,
            ForeignKey("consultations.id", ondelete="RESTRICT"),
            nullable=True,
            index=True,
        )
    )
    queue_entry_id: int | None = Field(
        default=None,
        sa_column=Column(
            Integer,
            ForeignKey("queue_entries.id", ondelete="RESTRICT"),
            nullable=True,
            index=True,
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
    doctor_user_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("auth_users.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        )
    )
    chief_complaint: str = Field(default="", sa_column=Column(Text, nullable=False))
    anamnesis: str = Field(default="", sa_column=Column(Text, nullable=False))
    diagnosis: str = Field(default="", sa_column=Column(Text, nullable=False))
    conduct_notes: str = Field(default="", sa_column=Column(Text, nullable=False))
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
    )
