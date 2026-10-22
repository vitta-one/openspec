"""Add persistent weekly professional shifts and provenance of generated slots.

Revision ID: a1d5b7e6c908
Revises: e6c0b1a4d209
"""
from alembic import op
import sqlalchemy as sa
revision = "a1d5b7e6c908"
down_revision = "e6c0b1a4d209"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "professional_weekly_schedules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("professional_id", sa.Integer(), nullable=False),
        sa.Column("weekday_start", sa.Integer(), nullable=False),
        sa.Column("weekday_end", sa.Integer(), nullable=False),
        sa.Column("time_start", sa.String(5), nullable=False),
        sa.Column("time_end", sa.String(5), nullable=False),
        sa.Column("slot_minutes", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["professional_id"], ["professionals.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("professional_id", name="uq_weekly_schedule_professional"),
        sa.CheckConstraint("weekday_start BETWEEN 0 AND 6", name="ck_weekly_start_day"),
        sa.CheckConstraint("weekday_end BETWEEN 0 AND 6", name="ck_weekly_end_day"),
        sa.CheckConstraint("weekday_end >= weekday_start", name="ck_weekly_day_order"),
        sa.CheckConstraint("slot_minutes IN (30, 60)", name="ck_weekly_slot_minutes"),
    )
    op.create_index("ix_professional_weekly_schedules_professional_id",
                    "professional_weekly_schedules", ["professional_id"], unique=True)
    op.add_column("professional_availability_slots",
                  sa.Column("is_weekly_generated", sa.Boolean(), nullable=False, server_default=sa.false()))

def downgrade() -> None:
    # Existing booked visits remain intact, but shift rules are lost on downgrade.
    op.drop_column("professional_availability_slots", "is_weekly_generated")
    op.drop_index("ix_professional_weekly_schedules_professional_id", table_name="professional_weekly_schedules")
    op.drop_table("professional_weekly_schedules")
