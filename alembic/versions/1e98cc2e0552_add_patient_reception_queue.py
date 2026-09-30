"""add patient reception queue

Revision ID: 1e98cc2e0552
Revises: eb45204dcb23
Create Date: 2026-09-29 01:17:55.274189

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

revision: str = "1e98cc2e0552"
down_revision: Union[str, Sequence[str], None] = "eb45204dcb23"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create patient and reception queue tables."""
    op.create_table(
        "patients",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("cpf", sa.String(length=11), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("patients", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_patients_cpf"), ["cpf"], unique=True)

    op.create_table(
        "queue_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("symptoms", sa.Text(), nullable=False),
        sa.Column("priority", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("entered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("doctor_user_id", sa.Integer(), nullable=True),
        sa.Column("called_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("withdrawn_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("withdrawal_reason", sa.String(length=300), nullable=True),
        sa.CheckConstraint(
            "priority IN ('VERMELHO', 'AMARELO', 'VERDE')",
            name="ck_queue_entries_priority",
        ),
        sa.CheckConstraint(
            "status IN ('AGUARDANDO', 'EM_ATENDIMENTO', 'FINALIZADO', 'RETIRADO')",
            name="ck_queue_entries_status",
        ),
        sa.ForeignKeyConstraint(
            ["doctor_user_id"], ["auth_users.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["patient_id"], ["patients.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("queue_entries", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_queue_entries_doctor_user_id"),
            ["doctor_user_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_queue_entries_entered_at"),
            ["entered_at"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_queue_entries_patient_id"),
            ["patient_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_queue_entries_priority"),
            ["priority"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_queue_entries_status"),
            ["status"],
            unique=False,
        )


def downgrade() -> None:
    """Remove patient and reception queue tables."""
    with op.batch_alter_table("queue_entries", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_queue_entries_status"))
        batch_op.drop_index(batch_op.f("ix_queue_entries_priority"))
        batch_op.drop_index(batch_op.f("ix_queue_entries_patient_id"))
        batch_op.drop_index(batch_op.f("ix_queue_entries_entered_at"))
        batch_op.drop_index(batch_op.f("ix_queue_entries_doctor_user_id"))

    op.drop_table("queue_entries")

    with op.batch_alter_table("patients", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_patients_cpf"))

    op.drop_table("patients")
