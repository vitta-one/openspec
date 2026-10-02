"""add clinical care records

Revision ID: a6b3c9d2e5f1
Revises: d4c7f8a2b1e6
Create Date: 2026-10-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a6b3c9d2e5f1"
down_revision: Union[str, Sequence[str], None] = "d4c7f8a2b1e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "clinical_care_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("consultation_id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("doctor_user_id", sa.Integer(), nullable=False),
        sa.Column("chief_complaint", sa.Text(), nullable=False),
        sa.Column("anamnesis", sa.Text(), nullable=False),
        sa.Column("diagnosis", sa.Text(), nullable=False),
        sa.Column("conduct_notes", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["consultation_id"], ["consultations.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["doctor_user_id"], ["auth_users.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "consultation_id",
            name="uq_clinical_care_records_consultation_id",
        ),
    )
    op.create_index(
        op.f("ix_clinical_care_records_consultation_id"),
        "clinical_care_records",
        ["consultation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_clinical_care_records_patient_id"),
        "clinical_care_records",
        ["patient_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_clinical_care_records_doctor_user_id"),
        "clinical_care_records",
        ["doctor_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_clinical_care_records_updated_at"),
        "clinical_care_records",
        ["updated_at"],
        unique=False,
    )
    op.create_index(
        "ix_clinical_care_records_patient_updated",
        "clinical_care_records",
        ["patient_id", "updated_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_clinical_care_records_patient_updated",
        table_name="clinical_care_records",
    )
    op.drop_index(
        op.f("ix_clinical_care_records_updated_at"),
        table_name="clinical_care_records",
    )
    op.drop_index(
        op.f("ix_clinical_care_records_doctor_user_id"),
        table_name="clinical_care_records",
    )
    op.drop_index(
        op.f("ix_clinical_care_records_patient_id"),
        table_name="clinical_care_records",
    )
    op.drop_index(
        op.f("ix_clinical_care_records_consultation_id"),
        table_name="clinical_care_records",
    )
    op.drop_table("clinical_care_records")
