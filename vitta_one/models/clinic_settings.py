"""Persisted single-clinic institutional details and their audit trail."""

from datetime import datetime, timezone

import reflex as rx
from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, String, text
from sqlmodel import Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ClinicConfiguration(rx.Model, table=True):
    """One configuration row for the clinic; Vitta One remains the system brand."""

    __tablename__ = "clinic_configurations"
    __table_args__ = (
        CheckConstraint("id = 1", name="ck_clinic_configurations_singleton"),
        CheckConstraint("revision >= 1", name="ck_clinic_configurations_revision"),
    )

    name: str = Field(sa_column=Column(String(160), nullable=False))
    address: str = Field(sa_column=Column(String(500), nullable=False))
    revision: int = Field(
        default=1, sa_column=Column(Integer, nullable=False, server_default=text("1"))
    )
    updated_at: datetime = Field(
        default_factory=utc_now, sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    updated_by_user_id: int | None = Field(
        default=None,
        sa_column=Column(
            Integer, ForeignKey("auth_users.id", ondelete="SET NULL"), nullable=True
        ),
    )


class ClinicConfigurationChange(rx.Model, table=True):
    """Append-only evidence of successful institutional configuration changes."""

    __tablename__ = "clinic_configuration_changes"

    previous_name: str | None = Field(
        default=None, sa_column=Column(String(160), nullable=True)
    )
    previous_address: str | None = Field(
        default=None, sa_column=Column(String(500), nullable=True)
    )
    name: str = Field(sa_column=Column(String(160), nullable=False))
    address: str = Field(sa_column=Column(String(500), nullable=False))
    actor_user_id: int | None = Field(
        default=None,
        sa_column=Column(
            Integer, ForeignKey("auth_users.id", ondelete="SET NULL"), nullable=True
        ),
    )
    occurred_at: datetime = Field(
        default_factory=utc_now, sa_column=Column(DateTime(timezone=True), nullable=False)
    )
