"""create user_profile

Revision ID: 0001_user_profile
Revises:
Create Date: 2026-06-21

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_user_profile"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_profile",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("identity_provider_id", sa.Text(), nullable=False),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("phone_number", sa.Text(), nullable=True),
        sa.Column(
            "default_role",
            sa.Enum("player", "organizer", "admin", name="user_role", native_enum=False),
            server_default="player",
            nullable=False,
        ),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_profile")),
    )
    op.create_index(
        op.f("ix_user_profile_identity_provider_id"),
        "user_profile",
        ["identity_provider_id"],
        unique=True,
    )
    op.create_index(op.f("ix_user_profile_email"), "user_profile", ["email"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_user_profile_email"), table_name="user_profile")
    op.drop_index(op.f("ix_user_profile_identity_provider_id"), table_name="user_profile")
    op.drop_table("user_profile")
