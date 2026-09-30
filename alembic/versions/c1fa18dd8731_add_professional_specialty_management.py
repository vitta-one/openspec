"""add professional specialty management

Revision ID: c1fa18dd8731
Revises: 1e98cc2e0552
Create Date: 2026-09-30 01:54:58.720300

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

revision: str = "c1fa18dd8731"
down_revision: Union[str, Sequence[str], None] = "1e98cc2e0552"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create professional and specialty directory tables."""
    op.create_table(
        "specialties",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("normalized_name", sa.String(length=120), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("specialties", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_specialties_is_active"), ["is_active"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_specialties_normalized_name"),
            ["normalized_name"],
            unique=True,
        )

    op.create_table(
        "professionals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("registration_identifier", sa.String(length=80), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["auth_users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("professionals", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_professionals_is_active"), ["is_active"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_professionals_registration_identifier"),
            ["registration_identifier"],
            unique=True,
        )
        batch_op.create_index(
            batch_op.f("ix_professionals_user_id"), ["user_id"], unique=True
        )

    op.create_table(
        "professional_specialties",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("professional_id", sa.Integer(), nullable=False),
        sa.Column("specialty_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["professional_id"], ["professionals.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["specialty_id"], ["specialties.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "professional_id",
            "specialty_id",
            name="uq_professional_specialties_pair",
        ),
    )
    with op.batch_alter_table("professional_specialties", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_professional_specialties_professional_id"),
            ["professional_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_professional_specialties_specialty_id"),
            ["specialty_id"],
            unique=False,
        )


def downgrade() -> None:
    """Remove professional and specialty directory tables."""
    with op.batch_alter_table("professional_specialties", schema=None) as batch_op:
        batch_op.drop_index(
            batch_op.f("ix_professional_specialties_specialty_id")
        )
        batch_op.drop_index(
            batch_op.f("ix_professional_specialties_professional_id")
        )

    op.drop_table("professional_specialties")

    with op.batch_alter_table("professionals", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_professionals_user_id"))
        batch_op.drop_index(
            batch_op.f("ix_professionals_registration_identifier")
        )
        batch_op.drop_index(batch_op.f("ix_professionals_is_active"))

    op.drop_table("professionals")

    with op.batch_alter_table("specialties", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_specialties_normalized_name"))
        batch_op.drop_index(batch_op.f("ix_specialties_is_active"))

    op.drop_table("specialties")
