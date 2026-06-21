"""Gym and Court ORM models (see docs/DATA_MODEL.md)."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class Gym(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "gym"

    name: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text, default="", server_default="")
    address_line_1: Mapped[str] = mapped_column(Text)
    address_line_2: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str] = mapped_column(Text)
    state: Mapped[str] = mapped_column(Text)
    postal_code: Mapped[str] = mapped_column(Text)
    # IANA timezone (e.g. America/New_York); drives display of run times.
    timezone: Mapped[str] = mapped_column(Text)
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("user_profile.id"),
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    courts: Mapped[list[Court]] = relationship(back_populates="gym", cascade="all, delete-orphan")


class Court(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "court"

    gym_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("gym.id"),
        index=True,
    )
    name: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    gym: Mapped[Gym] = relationship(back_populates="courts")
