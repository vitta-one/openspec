"""Persistent prescription models produced by one clinical care record."""

from datetime import datetime, timezone

import reflex as rx
from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlmodel import Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Prescription(rx.Model, table=True):
    """One printable prescription document authored during clinical care."""

    __tablename__ = "prescriptions"
    __table_args__ = (
        Index(
            "ix_prescriptions_record_created",
            "clinical_care_record_id",
            "created_at",
        ),
        Index(
            "ix_prescriptions_consultation_created",
            "consultation_id",
            "created_at",
        ),
    )

    clinical_care_record_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("clinical_care_records.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        )
    )
    consultation_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("consultations.id", ondelete="RESTRICT"),
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
    general_notes: str = Field(default="", sa_column=Column(Text, nullable=False))
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class PrescriptionItem(rx.Model, table=True):
    """One medication/item plus its free-text usage instructions."""

    __tablename__ = "prescription_items"
    __table_args__ = (
        Index(
            "ix_prescription_items_prescription_created",
            "prescription_id",
            "created_at",
        ),
    )

    prescription_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("prescriptions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    medication_or_item: str = Field(
        sa_column=Column(String(300), nullable=False)
    )
    instructions: str = Field(sa_column=Column(Text, nullable=False))
    notes: str = Field(default="", sa_column=Column(Text, nullable=False))
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
