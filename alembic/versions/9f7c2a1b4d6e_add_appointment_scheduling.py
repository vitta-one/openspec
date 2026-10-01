"""add appointment scheduling

Revision ID: 9f7c2a1b4d6e
Revises: c1fa18dd8731
Create Date: 2026-10-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "9f7c2a1b4d6e"
down_revision: Union[str, Sequence[str], None] = "c1fa18dd8731"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "professional_availability_slots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("professional_id", sa.Integer(), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('AVAILABLE', 'BOOKED', 'INACTIVE')",
            name="ck_availability_slot_status",
        ),
        sa.ForeignKeyConstraint(
            ["professional_id"], ["professionals.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "professional_id",
            "starts_at",
            name="uq_availability_professional_starts_at",
        ),
    )
    op.create_index(
        "ix_availability_professional_starts_at",
        "professional_availability_slots",
        ["professional_id", "starts_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_professional_availability_slots_professional_id"),
        "professional_availability_slots",
        ["professional_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_professional_availability_slots_starts_at"),
        "professional_availability_slots",
        ["starts_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_professional_availability_slots_status"),
        "professional_availability_slots",
        ["status"],
        unique=False,
    )

    op.create_table(
        "consultations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("professional_id", sa.Integer(), nullable=False),
        sa.Column("availability_slot_id", sa.Integer(), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('AGENDADA', 'CONFIRMADA', 'EM_ANDAMENTO', 'CONCLUIDA', 'CANCELADA')",
            name="ck_consultations_status",
        ),
        sa.ForeignKeyConstraint(
            ["availability_slot_id"],
            ["professional_availability_slots.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["professional_id"], ["professionals.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_consultations_availability_slot_id"),
        "consultations",
        ["availability_slot_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_consultations_patient_id"),
        "consultations",
        ["patient_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_consultations_professional_id"),
        "consultations",
        ["professional_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_consultations_scheduled_at"),
        "consultations",
        ["scheduled_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_consultations_status"),
        "consultations",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_consultations_professional_scheduled",
        "consultations",
        ["professional_id", "scheduled_at"],
        unique=False,
    )
    op.create_index(
        "ix_consultations_status_scheduled",
        "consultations",
        ["status", "scheduled_at"],
        unique=False,
    )
    op.create_index(
        "uq_consultations_active_slot",
        "consultations",
        ["availability_slot_id"],
        unique=True,
        postgresql_where=sa.text("status <> 'CANCELADA'"),
    )


def downgrade() -> None:
    op.drop_index("uq_consultations_active_slot", table_name="consultations")
    op.drop_index("ix_consultations_status_scheduled", table_name="consultations")
    op.drop_index("ix_consultations_professional_scheduled", table_name="consultations")
    op.drop_index(op.f("ix_consultations_status"), table_name="consultations")
    op.drop_index(op.f("ix_consultations_scheduled_at"), table_name="consultations")
    op.drop_index(op.f("ix_consultations_professional_id"), table_name="consultations")
    op.drop_index(op.f("ix_consultations_patient_id"), table_name="consultations")
    op.drop_index(op.f("ix_consultations_availability_slot_id"), table_name="consultations")
    op.drop_table("consultations")

    op.drop_index(
        op.f("ix_professional_availability_slots_status"),
        table_name="professional_availability_slots",
    )
    op.drop_index(
        op.f("ix_professional_availability_slots_starts_at"),
        table_name="professional_availability_slots",
    )
    op.drop_index(
        op.f("ix_professional_availability_slots_professional_id"),
        table_name="professional_availability_slots",
    )
    op.drop_index(
        "ix_availability_professional_starts_at",
        table_name="professional_availability_slots",
    )
    op.drop_table("professional_availability_slots")
