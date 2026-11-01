"""Persist employee display names without changing existing identities.

Revision ID: 7c4f9a3d2b10
Revises: a1d5b7e6c908
"""

from alembic import op
import sqlalchemy as sa

revision = "7c4f9a3d2b10"
down_revision = "a1d5b7e6c908"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("auth_users", sa.Column("display_name", sa.String(160), nullable=True))


def downgrade() -> None:
    # Downgrade drops staff names. Only reverse in a backed-up QA database.
    op.drop_column("auth_users", "display_name")
