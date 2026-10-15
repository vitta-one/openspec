"""Add an optional contact phone to patient identity.

Revision ID: c62ab3f1e907
Revises: f2a4c9d8e721
Create Date: 2026-10-15
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c62ab3f1e907"
down_revision: Union[str, Sequence[str], None] = "f2a4c9d8e721"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "patients",
        sa.Column("phone", sa.String(length=11), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("patients", "phone")
