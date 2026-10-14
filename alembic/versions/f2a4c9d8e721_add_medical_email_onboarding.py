"""Add safe temporary credentials and email acceptance status.

Revision ID: f2a4c9d8e721
Revises: b7d4e1f6a2c8
Create Date: 2026-10-14
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f2a4c9d8e721"
down_revision: Union[str, Sequence[str], None] = "b7d4e1f6a2c8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Backfill existing identities as ordinary accounts. No password reset.
    op.add_column(
        "auth_users",
        sa.Column("must_change_password", sa.Boolean(),
                  nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "auth_users",
        sa.Column("temporary_password_expires_at", sa.DateTime(timezone=True),
                  nullable=True),
    )
    op.add_column(
        "professionals",
        sa.Column("onboarding_email_status", sa.String(32), nullable=False,
                  server_default="NOT_REQUIRED"),
    )
    op.add_column(
        "professionals",
        sa.Column("onboarding_email_message_id", sa.String(128), nullable=True),
    )


def downgrade() -> None:
    # Only for disposable QA databases with confirmed backups. No auto-downgrade.
    op.drop_column("professionals", "onboarding_email_message_id")
    op.drop_column("professionals", "onboarding_email_status")
    op.drop_column("auth_users", "temporary_password_expires_at")
    op.drop_column("auth_users", "must_change_password")
