"""Private clinical exam and attachment persistence."""

from datetime import date, datetime, timezone

import reflex as rx
from sqlalchemy import Boolean, CheckConstraint, Column, Date, DateTime, ForeignKey, Index, Integer, String, Text
from sqlmodel import Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ClinicalAttachment(rx.Model, table=True):
    """Metadata for one private file stored outside PostgreSQL."""

    __tablename__ = "clinical_attachments"
    __table_args__ = (
        CheckConstraint(
            "status IN ('ACTIVE', 'DELETION_FAILED', 'REMOVED')",
            name="ck_clinical_attachments_status",
        ),
        CheckConstraint("byte_size > 0", name="ck_clinical_attachments_byte_size"),
        Index("ix_clinical_attachments_patient_created", "patient_id", "created_at"),
        Index("ix_clinical_attachments_record_created", "clinical_care_record_id", "created_at"),
    )

    patient_id: int = Field(
        sa_column=Column(Integer, ForeignKey("patients.id", ondelete="RESTRICT"), nullable=False, index=True)
    )
    consultation_id: int | None = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("consultations.id", ondelete="RESTRICT"), nullable=True, index=True),
    )
    clinical_care_record_id: int | None = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("clinical_care_records.id", ondelete="RESTRICT"), nullable=True, index=True),
    )
    uploaded_by_user_id: int = Field(
        sa_column=Column(Integer, ForeignKey("auth_users.id", ondelete="RESTRICT"), nullable=False, index=True)
    )
    title: str = Field(sa_column=Column(String(160), nullable=False))
    category: str = Field(sa_column=Column(String(40), nullable=False, index=True))
    exam_date: date | None = Field(default=None, sa_column=Column(Date, nullable=True))
    original_filename: str = Field(sa_column=Column(String(255), nullable=False))
    content_type: str = Field(sa_column=Column(String(100), nullable=False))
    byte_size: int = Field(sa_column=Column(Integer, nullable=False))
    cloud_asset_id: str = Field(sa_column=Column(String(255), nullable=False, unique=True, index=True))
    cloud_public_id: str = Field(sa_column=Column(String(255), nullable=False, unique=True, index=True))
    cloud_version: int = Field(sa_column=Column(Integer, nullable=False))
    cloud_resource_type: str = Field(sa_column=Column(String(20), nullable=False))
    cloud_format: str = Field(sa_column=Column(String(20), nullable=False))
    status: str = Field(default="ACTIVE", sa_column=Column(String(24), nullable=False, index=True))
    patient_visible: bool = Field(default=False, sa_column=Column(Boolean, nullable=False, index=True))
    created_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), nullable=False, index=True))
    updated_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), nullable=False))
    removed_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))


class ClinicalAttachmentAudit(rx.Model, table=True):
    """Minimal audit trail; never stores file content or signed URLs."""

    __tablename__ = "clinical_attachment_audits"
    __table_args__ = (Index("ix_clinical_attachment_audits_attachment_created", "attachment_id", "created_at"),)

    attachment_id: int = Field(
        sa_column=Column(Integer, ForeignKey("clinical_attachments.id", ondelete="RESTRICT"), nullable=False, index=True)
    )
    actor_user_id: int | None = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("auth_users.id", ondelete="SET NULL"), nullable=True, index=True),
    )
    action: str = Field(sa_column=Column(String(40), nullable=False))
    outcome: str = Field(sa_column=Column(String(24), nullable=False))
    detail_code: str = Field(default="", sa_column=Column(String(80), nullable=False))
    created_at: datetime = Field(default_factory=utc_now, sa_column=Column(DateTime(timezone=True), nullable=False, index=True))

