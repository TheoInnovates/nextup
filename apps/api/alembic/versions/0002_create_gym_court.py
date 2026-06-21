"""create gym and court

Revision ID: 0002_gym_court
Revises: 0001_user_profile
Create Date: 2026-06-21

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_gym_court"
down_revision: str | None = "0001_user_profile"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "gym",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), server_default="", nullable=False),
        sa.Column("address_line_1", sa.Text(), nullable=False),
        sa.Column("address_line_2", sa.Text(), nullable=True),
        sa.Column("city", sa.Text(), nullable=False),
        sa.Column("state", sa.Text(), nullable=False),
        sa.Column("postal_code", sa.Text(), nullable=False),
        sa.Column("timezone", sa.Text(), nullable=False),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_gym")),
        sa.ForeignKeyConstraint(
            ["owner_user_id"],
            ["user_profile.id"],
            name=op.f("fk_gym_owner_user_id_user_profile"),
        ),
    )
    op.create_index(op.f("ix_gym_owner_user_id"), "gym", ["owner_user_id"])

    op.create_table(
        "court",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("gym_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_court")),
        sa.ForeignKeyConstraint(["gym_id"], ["gym.id"], name=op.f("fk_court_gym_id_gym")),
    )
    op.create_index(op.f("ix_court_gym_id"), "court", ["gym_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_court_gym_id"), table_name="court")
    op.drop_table("court")
    op.drop_index(op.f("ix_gym_owner_user_id"), table_name="gym")
    op.drop_table("gym")
