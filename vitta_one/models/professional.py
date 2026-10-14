"""Persistent professional and specialty directory models."""

from datetime import datetime, timezone

import reflex as rx
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlmodel import Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Specialty(rx.Model, table=True):
    """A clinic specialty managed by administrators."""

    __tablename__ = "specialties"

    name: str = Field(sa_column=Column(String(120), nullable=False))
    normalized_name: str = Field(
        sa_column=Column(String(120), nullable=False, unique=True, index=True)
    )
    is_active: bool = Field(
        default=True,
        sa_column=Column(Boolean, nullable=False, index=True, default=True),
    )
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class Professional(rx.Model, table=True):
    """A clinic professional prepared for future scheduling and consultation flows."""

    __tablename__ = "professionals"

    name: str = Field(sa_column=Column(String(160), nullable=False))
    registration_identifier: str = Field(
        sa_column=Column(String(80), nullable=False, unique=True, index=True)
    )
    onboarding_email_status: str = Field(
        default="NOT_REQUIRED",
        sa_column=Column(String(32), nullable=False, server_default="NOT_REQUIRED"),
    )
    onboarding_email_message_id: str | None = Field(
        default=None, sa_column=Column(String(128), nullable=True)
    )
    is_active: bool = Field(
        default=True,
        sa_column=Column(Boolean, nullable=False, index=True, default=True),
    )
    user_id: int | None = Field(
        default=None,
        sa_column=Column(
            Integer,
            ForeignKey("auth_users.id", ondelete="SET NULL"),
            nullable=True,
            unique=True,
            index=True,
        ),
    )
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class ProfessionalSpecialty(rx.Model, table=True):
    """Many-to-many association between professionals and specialties."""

    __tablename__ = "professional_specialties"
    __table_args__ = (
        UniqueConstraint(
            "professional_id",
            "specialty_id",
            name="uq_professional_specialties_pair",
        ),
    )

    professional_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("professionals.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    specialty_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("specialties.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        )
    )
