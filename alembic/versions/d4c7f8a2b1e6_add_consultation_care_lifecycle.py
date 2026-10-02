"""add consultation care lifecycle

Revision ID: d4c7f8a2b1e6
Revises: 9f7c2a1b4d6e
Create Date: 2026-10-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "d4c7f8a2b1e6"
down_revision: Union[str, Sequence[str], None] = "9f7c2a1b4d6e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("consultations", sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("consultations", sa.Column("started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("consultations", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True))

    op.add_column("queue_entries", sa.Column("consultation_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_queue_entries_consultation_id_consultations",
        "queue_entries",
        "consultations",
        ["consultation_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        op.f("ix_queue_entries_consultation_id"),
        "queue_entries",
        ["consultation_id"],
        unique=False,
    )
    op.create_unique_constraint(
        "uq_queue_entries_consultation_id",
        "queue_entries",
        ["consultation_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_queue_entries_consultation_id", "queue_entries", type_="unique")
    op.drop_index(op.f("ix_queue_entries_consultation_id"), table_name="queue_entries")
    op.drop_constraint(
        "fk_queue_entries_consultation_id_consultations",
        "queue_entries",
        type_="foreignkey",
    )
    op.drop_column("queue_entries", "consultation_id")

    op.drop_column("consultations", "completed_at")
    op.drop_column("consultations", "started_at")
    op.drop_column("consultations", "confirmed_at")
