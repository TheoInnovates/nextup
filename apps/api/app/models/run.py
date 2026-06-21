"""BasketballRun ORM model (see docs/DATA_MODEL.md).

All timestamps are stored in UTC (``timestamptz``); display conversion to the
gym's timezone happens in the frontend.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.enums import RunStatus


class BasketballRun(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "basketball_run"

    gym_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("gym.id"), index=True
    )
    organizer_user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("user_profile.id"), index=True
    )
    title: Mapped[str] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    registration_opens_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    registration_closes_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    cancellation_deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    maximum_players: Mapped[int] = mapped_column(Integer)
    players_per_team: Mapped[int] = mapped_column(Integer)
    number_of_courts: Mapped[int] = mapped_column(Integer)
    estimated_game_minutes: Mapped[int] = mapped_column(Integer)
    arrival_lead_minutes: Mapped[int] = mapped_column(Integer)

    status: Mapped[RunStatus] = mapped_column(
        SAEnum(RunStatus, name="run_status", native_enum=False),
        default=RunStatus.draft,
        server_default=RunStatus.draft.value,
        index=True,
    )

    gym = relationship("Gym")

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"<BasketballRun {self.title!r} ({self.status})>"
