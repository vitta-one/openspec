"""add clinical prescriptions

Revision ID: b7d4e1f6a2c8
Revises: a6b3c9d2e5f1
Create Date: 2026-10-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "b7d4e1f6a2c8"
down_revision: Union[str, Sequence[str], None] = "a6b3c9d2e5f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "prescriptions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("clinical_care_record_id", sa.Integer(), nullable=False),
        sa.Column("consultation_id", sa.Integer(), nullable=False),
        sa.Column("doctor_user_id", sa.Integer(), nullable=False),
        sa.Column("general_notes", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["clinical_care_record_id"],
            ["clinical_care_records.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["consultation_id"], ["consultations.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["doctor_user_id"], ["auth_users.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_prescriptions_clinical_care_record_id"),
        "prescriptions",
        ["clinical_care_record_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_prescriptions_consultation_id"),
        "prescriptions",
        ["consultation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_prescriptions_doctor_user_id"),
        "prescriptions",
        ["doctor_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_prescriptions_created_at"),
        "prescriptions",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_prescriptions_record_created",
        "prescriptions",
        ["clinical_care_record_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_prescriptions_consultation_created",
        "prescriptions",
        ["consultation_id", "created_at"],
        unique=False,
    )

    op.create_table(
        "prescription_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("prescription_id", sa.Integer(), nullable=False),
        sa.Column("medication_or_item", sa.String(length=300), nullable=False),
        sa.Column("instructions", sa.Text(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["prescription_id"], ["prescriptions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_prescription_items_prescription_id"),
        "prescription_items",
        ["prescription_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_prescription_items_created_at"),
        "prescription_items",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_prescription_items_prescription_created",
        "prescription_items",
        ["prescription_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_prescription_items_prescription_created",
        table_name="prescription_items",
    )
    op.drop_index(
        op.f("ix_prescription_items_created_at"),
        table_name="prescription_items",
    )
    op.drop_index(
        op.f("ix_prescription_items_prescription_id"),
        table_name="prescription_items",
    )
    op.drop_table("prescription_items")

    op.drop_index(
        "ix_prescriptions_consultation_created",
        table_name="prescriptions",
    )
    op.drop_index(
        "ix_prescriptions_record_created",
        table_name="prescriptions",
    )
    op.drop_index(op.f("ix_prescriptions_created_at"), table_name="prescriptions")
    op.drop_index(op.f("ix_prescriptions_doctor_user_id"), table_name="prescriptions")
    op.drop_index(op.f("ix_prescriptions_consultation_id"), table_name="prescriptions")
    op.drop_index(
        op.f("ix_prescriptions_clinical_care_record_id"),
        table_name="prescriptions",
    )
    op.drop_table("prescriptions")
