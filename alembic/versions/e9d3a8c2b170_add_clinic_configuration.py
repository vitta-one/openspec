"""Persist institutional clinic configuration and change history.

Revision ID: e9d3a8c2b170
Revises: 7c4f9a3d2b10
Create Date: 2026-10-31
"""
from alembic import op
import sqlalchemy as sa

revision = "e9d3a8c2b170"
down_revision = "7c4f9a3d2b10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "clinic_configurations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("address", sa.String(500), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_by_user_id", sa.Integer(), nullable=True),
        sa.CheckConstraint("id = 1", name="ck_clinic_configurations_singleton"),
        sa.CheckConstraint("revision >= 1", name="ck_clinic_configurations_revision"),
        sa.ForeignKeyConstraint(
            ["updated_by_user_id"], ["auth_users.id"], ondelete="SET NULL"
        ),
    )
    op.create_table(
        "clinic_configuration_changes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("previous_name", sa.String(160), nullable=True),
        sa.Column("previous_address", sa.String(500), nullable=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("address", sa.String(500), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["actor_user_id"], ["auth_users.id"], ondelete="SET NULL"
        ),
    )


def downgrade() -> None:
    # Execute only in disposable QA: rollback removes saved settings and history.
    op.drop_table("clinic_configuration_changes")
    op.drop_table("clinic_configurations")
