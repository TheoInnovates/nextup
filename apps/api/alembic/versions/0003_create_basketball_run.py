"""create basketball_run

Revision ID: 0003_basketball_run
Revises: 0002_gym_court
Create Date: 2026-06-21

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_basketball_run"
down_revision: str | None = "0002_gym_court"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_RUN_STATUS = sa.Enum(
    "draft",
    "published",
    "registration_closed",
    "in_progress",
    "completed",
    "cancelled",
    name="run_status",
    native_enum=False,
)


def upgrade() -> None:
    op.create_table(
        "basketball_run",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("gym_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organizer_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("registration_opens_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("registration_closes_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("cancellation_deadline", sa.DateTime(timezone=True), nullable=False),
        sa.Column("maximum_players", sa.Integer(), nullable=False),
        sa.Column("players_per_team", sa.Integer(), nullable=False),
        sa.Column("number_of_courts", sa.Integer(), nullable=False),
        sa.Column("estimated_game_minutes", sa.Integer(), nullable=False),
        sa.Column("arrival_lead_minutes", sa.Integer(), nullable=False),
        sa.Column("status", _RUN_STATUS, server_default="draft", nullable=False),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_basketball_run")),
        sa.ForeignKeyConstraint(["gym_id"], ["gym.id"], name=op.f("fk_basketball_run_gym_id_gym")),
        sa.ForeignKeyConstraint(
            ["organizer_user_id"],
            ["user_profile.id"],
            name=op.f("fk_basketball_run_organizer_user_id_user_profile"),
        ),
    )
    op.create_index(op.f("ix_basketball_run_gym_id"), "basketball_run", ["gym_id"])
    op.create_index(
        op.f("ix_basketball_run_organizer_user_id"),
        "basketball_run",
        ["organizer_user_id"],
    )
    op.create_index(op.f("ix_basketball_run_status"), "basketball_run", ["status"])


def downgrade() -> None:
    op.drop_index(op.f("ix_basketball_run_status"), table_name="basketball_run")
    op.drop_index(op.f("ix_basketball_run_organizer_user_id"), table_name="basketball_run")
    op.drop_index(op.f("ix_basketball_run_gym_id"), table_name="basketball_run")
    op.drop_table("basketball_run")
