"""Initial schema.

Revision ID: 0001_initial
Revises:
Create Date: 2026-11-08

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=64), nullable=True),
        sa.Column("full_name", sa.String(length=128), nullable=False),
        sa.Column("phone_number", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "services",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(length=128), nullable=False),
        sa.Column("price", sa.Integer(), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "booking_slots",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("start_time", sa.DateTime(), nullable=False),
        sa.Column("is_booked", sa.Boolean(), nullable=False),
        sa.Column("service_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(
            ["service_id"], ["services.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_booking_slots_start_time",
        "booking_slots",
        ["start_time"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_booking_slots_start_time", table_name="booking_slots")
    op.drop_table("booking_slots")
    op.drop_table("services")
    op.drop_table("users")
