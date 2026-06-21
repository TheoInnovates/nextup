"""create notification and audit_event

Revision ID: 0005_notification_audit
Revises: 0004_run_registration
Create Date: 2026-06-21

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005_notification_audit"
down_revision: str | None = "0004_run_registration"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NOTIFICATION_TYPE = sa.Enum(
    "waitlist_promoted",
    "run_cancelled",
    "time_changed",
    "registration_confirmed",
    name="notification_type",
    native_enum=False,
)


def upgrade() -> None:
    op.create_table(
        "notification",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", _NOTIFICATION_TYPE, nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("related_run_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_read", sa.Boolean(), server_default="false", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_notification")),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user_profile.id"],
            name=op.f("fk_notification_user_id_user_profile"),
        ),
        sa.ForeignKeyConstraint(
            ["related_run_id"],
            ["basketball_run.id"],
            name=op.f("fk_notification_related_run_id_basketball_run"),
        ),
    )
    op.create_index(op.f("ix_notification_user_id"), "notification", ["user_id"])
    op.create_index(op.f("ix_notification_created_at"), "notification", ["created_at"])

    op.create_table(
        "audit_event",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("entity_type", sa.Text(), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_event")),
        sa.ForeignKeyConstraint(
            ["actor_user_id"],
            ["user_profile.id"],
            name=op.f("fk_audit_event_actor_user_id_user_profile"),
        ),
    )
    op.create_index(op.f("ix_audit_event_event_type"), "audit_event", ["event_type"])
    op.create_index(op.f("ix_audit_event_entity_id"), "audit_event", ["entity_id"])
    op.create_index(op.f("ix_audit_event_created_at"), "audit_event", ["created_at"])


def downgrade() -> None:
    op.drop_index(op.f("ix_audit_event_created_at"), table_name="audit_event")
    op.drop_index(op.f("ix_audit_event_entity_id"), table_name="audit_event")
    op.drop_index(op.f("ix_audit_event_event_type"), table_name="audit_event")
    op.drop_table("audit_event")
    op.drop_index(op.f("ix_notification_created_at"), table_name="notification")
    op.drop_index(op.f("ix_notification_user_id"), table_name="notification")
    op.drop_table("notification")
