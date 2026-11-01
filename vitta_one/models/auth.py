"""Persistent authentication models."""

from datetime import datetime, timezone

import reflex as rx
from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, Integer, String, text
from sqlmodel import Field

from vitta_one.auth.roles import Role


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


class User(rx.Model, table=True):
    """Minimal local identity required for authentication and RBAC."""

    __tablename__ = "auth_users"
    __table_args__ = (
        CheckConstraint(
            "role IN ('ADMINISTRADOR', 'RECEPCIONISTA', 'MEDICO', 'FINANCEIRO', 'PACIENTE')",
            name="ck_auth_users_role",
        ),
    )

    email: str = Field(
        sa_column=Column(String(320), nullable=False, unique=True, index=True)
    )
    display_name: str | None = Field(default=None, sa_column=Column(String(160), nullable=True))
    password_hash: str = Field(sa_column=Column(String(512), nullable=False))
    role: str = Field(sa_column=Column(String(32), nullable=False))
    must_change_password: bool = Field(
        default=False,
        sa_column=Column(Boolean, nullable=False, server_default=text("false")),
    )
    temporary_password_expires_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )

    @property
    def parsed_role(self) -> Role:
        """Return the persisted role as the closed domain enum."""
        return Role(self.role)


class AuthSession(rx.Model, table=True):
    """Revocable server-side session linked to a local user."""

    __tablename__ = "auth_sessions"

    user_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("auth_users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    token_hash: str = Field(
        sa_column=Column(String(64), nullable=False, unique=True, index=True)
    )
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    expires_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True)
    )
    revoked_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
