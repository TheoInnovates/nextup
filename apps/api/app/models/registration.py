"""RunRegistration ORM model (see docs/DATA_MODEL.md).

At most one *active* registration per (run, player) — enforced by a partial
unique index over active statuses, so a player may re-register after cancelling
while cancelled/no-show rows are retained for audit.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, func, text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.enums import RegistrationStatus

# Statuses that occupy an "active" registration slot for uniqueness purposes.
ACTIVE_STATUS_SQL = "('confirmed', 'waitlisted', 'checked_in')"


class RunRegistration(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "run_registration"

    run_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("basketball_run.id"), index=True
    )
    player_user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("user_profile.id"), index=True
    )
    status: Mapped[RegistrationStatus] = mapped_column(
        SAEnum(RegistrationStatus, name="registration_status", native_enum=False),
        index=True,
    )
    queue_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    assigned_slot_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    assigned_arrival_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    estimated_play_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    checked_in_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index(
            "uq_active_registration_per_run_player",
            "run_id",
            "player_user_id",
            unique=True,
            postgresql_where=text(f"status IN {ACTIVE_STATUS_SQL}"),
        ),
    )

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"<RunRegistration run={self.run_id} player={self.player_user_id} {self.status}>"
