"""Allow clinical care for direct queue arrivals without removing scheduled consultations.

Revision ID: e6c0b1a4d209
Revises: 8c1d5e2f7a90
Create Date: 2026-10-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "e6c0b1a4d209"
down_revision: Union[str, Sequence[str], None] = "8c1d5e2f7a90"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "clinical_care_records",
        sa.Column("queue_entry_id", sa.Integer(), nullable=True),
    )
    op.alter_column(
        "clinical_care_records",
        "consultation_id",
        existing_type=sa.Integer(),
        nullable=True,
    )
    op.create_foreign_key(
        "fk_clinical_care_records_queue_entry",
        "clinical_care_records",
        "queue_entries",
        ["queue_entry_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        op.f("ix_clinical_care_records_queue_entry_id"),
        "clinical_care_records",
        ["queue_entry_id"],
        unique=False,
    )
    op.create_unique_constraint(
        "uq_clinical_care_records_queue_entry_id",
        "clinical_care_records",
        ["queue_entry_id"],
    )
    op.create_check_constraint(
        "ck_clinical_care_records_one_episode",
        "clinical_care_records",
        "(consultation_id IS NOT NULL AND queue_entry_id IS NULL) OR "
        "(consultation_id IS NULL AND queue_entry_id IS NOT NULL)",
    )
    op.alter_column(
        "prescriptions", "consultation_id", existing_type=sa.Integer(), nullable=True
    )


def downgrade() -> None:
    connection = op.get_bind()
    # Downgrading must never silently discard linked clinical content.
    count = connection.execute(
        sa.text("SELECT count(*) FROM clinical_care_records WHERE queue_entry_id IS NOT NULL")
    ).scalar_one()
    if count:
        raise RuntimeError(
            "Downgrade blocked: walk-in clinical records exist. "
            "Migrate their data explicitly before reversing this schema."
        )
    op.alter_column("prescriptions", "consultation_id", existing_type=sa.Integer(), nullable=False)
    op.drop_constraint(
        "ck_clinical_care_records_one_episode", "clinical_care_records", type_="check"
    )
    op.drop_constraint(
        "uq_clinical_care_records_queue_entry_id",
        "clinical_care_records",
        type_="unique",
    )
    op.drop_index(
        op.f("ix_clinical_care_records_queue_entry_id"),
        table_name="clinical_care_records",
    )
    op.drop_constraint(
        "fk_clinical_care_records_queue_entry",
        "clinical_care_records",
        type_="foreignkey",
    )
    op.drop_column("clinical_care_records", "queue_entry_id")
    op.alter_column(
        "clinical_care_records",
        "consultation_id",
        existing_type=sa.Integer(),
        nullable=False,
    )
