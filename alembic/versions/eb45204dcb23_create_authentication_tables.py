"""Create authentication tables.

Revision ID: eb45204dcb23
Revises:
Create Date: 2026-09-29 00:17:29.209929

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

revision: str = "eb45204dcb23"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the local authentication schema."""
    op.create_table(
        "auth_users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=512), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "role IN ('ADMINISTRADOR', 'RECEPCIONISTA', 'MEDICO', 'FINANCEIRO')",
            name="ck_auth_users_role",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("auth_users", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_auth_users_email"), ["email"], unique=True)

    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["auth_users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("auth_sessions", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_auth_sessions_expires_at"), ["expires_at"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_auth_sessions_token_hash"), ["token_hash"], unique=True
        )
        batch_op.create_index(
            batch_op.f("ix_auth_sessions_user_id"), ["user_id"], unique=False
        )


def downgrade() -> None:
    """Remove the local authentication schema."""
    with op.batch_alter_table("auth_sessions", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_auth_sessions_user_id"))
        batch_op.drop_index(batch_op.f("ix_auth_sessions_token_hash"))
        batch_op.drop_index(batch_op.f("ix_auth_sessions_expires_at"))

    op.drop_table("auth_sessions")

    with op.batch_alter_table("auth_users", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_auth_users_email"))

    op.drop_table("auth_users")
