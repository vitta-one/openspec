"""Add patient portal access and consultation schedule audit.

Revision ID: 8c1d5e2f7a90
Revises: c62ab3f1e907
Create Date: 2026-10-15
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8c1d5e2f7a90"
down_revision: Union[str, Sequence[str], None] = "c62ab3f1e907"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("auth_users") as batch_op:
        batch_op.drop_constraint("ck_auth_users_role", type_="check")
        batch_op.create_check_constraint(
            "ck_auth_users_role",
            "role IN ('ADMINISTRADOR', 'RECEPCIONISTA', 'MEDICO', 'FINANCEIRO', 'PACIENTE')",
        )

    with op.batch_alter_table("patients") as batch_op:
        batch_op.add_column(sa.Column("user_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_patients_user_id_auth_users", "auth_users",
            ["user_id"], ["id"], ondelete="SET NULL",
        )
    op.create_index("ix_patients_user_id", "patients", ["user_id"], unique=True)

    op.create_table(
        "patient_portal_invitations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("code_hash", sa.String(length=64), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("consented_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("delivery_status", sa.String(length=24), nullable=False),
        sa.Column("provider_message_id", sa.String(length=128), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["auth_users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_patient_portal_invitations_patient_id", "patient_portal_invitations", ["patient_id"])
    op.create_index("ix_patient_portal_invitations_email", "patient_portal_invitations", ["email"])
    op.create_index("ix_patient_portal_invitations_code_hash", "patient_portal_invitations", ["code_hash"], unique=True)
    op.create_index("ix_patient_portal_invitations_created_by_user_id", "patient_portal_invitations", ["created_by_user_id"])
    op.create_index("ix_patient_portal_invitations_created_at", "patient_portal_invitations", ["created_at"])
    op.create_index("ix_patient_portal_invitations_expires_at", "patient_portal_invitations", ["expires_at"])
    op.create_index("ix_patient_portal_invitations_delivery_status", "patient_portal_invitations", ["delivery_status"])

    op.create_table(
        "consultation_schedule_changes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("consultation_id", sa.Integer(), nullable=False),
        sa.Column("previous_scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("new_scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("changed_by_user_id", sa.Integer(), nullable=True),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["consultation_id"], ["consultations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["changed_by_user_id"], ["auth_users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_consultation_schedule_changes_consultation_id", "consultation_schedule_changes", ["consultation_id"])
    op.create_index("ix_consultation_schedule_changes_changed_by_user_id", "consultation_schedule_changes", ["changed_by_user_id"])
    op.create_index("ix_consultation_schedule_changes_changed_at", "consultation_schedule_changes", ["changed_at"])


def downgrade() -> None:
    connection = op.get_bind()
    linked_patients = connection.execute(
        sa.text("SELECT count(*) FROM patients WHERE user_id IS NOT NULL")
    ).scalar_one()
    patient_accounts = connection.execute(
        sa.text("SELECT count(*) FROM auth_users WHERE role = 'PACIENTE'")
    ).scalar_one()
    invitations = connection.execute(
        sa.text("SELECT count(*) FROM patient_portal_invitations")
    ).scalar_one()
    schedule_changes = connection.execute(
        sa.text("SELECT count(*) FROM consultation_schedule_changes")
    ).scalar_one()
    if linked_patients or patient_accounts or invitations or schedule_changes:
        raise RuntimeError(
            "Downgrade bloqueado: há contas, convites ou histórico que seriam perdidos."
        )

    op.drop_index("ix_consultation_schedule_changes_changed_at", table_name="consultation_schedule_changes")
    op.drop_index("ix_consultation_schedule_changes_changed_by_user_id", table_name="consultation_schedule_changes")
    op.drop_index("ix_consultation_schedule_changes_consultation_id", table_name="consultation_schedule_changes")
    op.drop_table("consultation_schedule_changes")

    op.drop_index("ix_patient_portal_invitations_delivery_status", table_name="patient_portal_invitations")
    op.drop_index("ix_patient_portal_invitations_expires_at", table_name="patient_portal_invitations")
    op.drop_index("ix_patient_portal_invitations_created_at", table_name="patient_portal_invitations")
    op.drop_index("ix_patient_portal_invitations_created_by_user_id", table_name="patient_portal_invitations")
    op.drop_index("ix_patient_portal_invitations_code_hash", table_name="patient_portal_invitations")
    op.drop_index("ix_patient_portal_invitations_email", table_name="patient_portal_invitations")
    op.drop_index("ix_patient_portal_invitations_patient_id", table_name="patient_portal_invitations")
    op.drop_table("patient_portal_invitations")

    op.drop_index("ix_patients_user_id", table_name="patients")
    with op.batch_alter_table("patients") as batch_op:
        batch_op.drop_constraint("fk_patients_user_id_auth_users", type_="foreignkey")
        batch_op.drop_column("user_id")
    with op.batch_alter_table("auth_users") as batch_op:
        batch_op.drop_constraint("ck_auth_users_role", type_="check")
        batch_op.create_check_constraint(
            "ck_auth_users_role",
            "role IN ('ADMINISTRADOR', 'RECEPCIONISTA', 'MEDICO', 'FINANCEIRO')",
        )
