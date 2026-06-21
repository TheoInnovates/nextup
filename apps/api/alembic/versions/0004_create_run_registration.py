"""create run_registration

Revision ID: 0004_run_registration
Revises: 0003_basketball_run
Create Date: 2026-06-21

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_run_registration"
down_revision: str | None = "0003_basketball_run"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_REG_STATUS = sa.Enum(
    "confirmed",
    "waitlisted",
    "checked_in",
    "cancelled",
    "no_show",
    "completed",
    name="registration_status",
    native_enum=False,
)


def upgrade() -> None:
    op.create_table(
        "run_registration",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("player_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", _REG_STATUS, nullable=False),
        sa.Column("queue_position", sa.Integer(), nullable=True),
        sa.Column("assigned_slot_number", sa.Integer(), nullable=True),
        sa.Column("assigned_arrival_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("estimated_play_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "registered_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("checked_in_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_run_registration")),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["basketball_run.id"],
            name=op.f("fk_run_registration_run_id_basketball_run"),
        ),
        sa.ForeignKeyConstraint(
            ["player_user_id"],
            ["user_profile.id"],
            name=op.f("fk_run_registration_player_user_id_user_profile"),
        ),
    )
    op.create_index(op.f("ix_run_registration_run_id"), "run_registration", ["run_id"])
    op.create_index(
        op.f("ix_run_registration_player_user_id"),
        "run_registration",
        ["player_user_id"],
    )
    op.create_index(op.f("ix_run_registration_status"), "run_registration", ["status"])
    # At most one active registration per (run, player).
    op.create_index(
        "uq_active_registration_per_run_player",
        "run_registration",
        ["run_id", "player_user_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('confirmed', 'waitlisted', 'checked_in')"),
    )


def downgrade() -> None:
    op.drop_index("uq_active_registration_per_run_player", table_name="run_registration")
    op.drop_index(op.f("ix_run_registration_status"), table_name="run_registration")
    op.drop_index(op.f("ix_run_registration_player_user_id"), table_name="run_registration")
    op.drop_index(op.f("ix_run_registration_run_id"), table_name="run_registration")
    op.drop_table("run_registration")
