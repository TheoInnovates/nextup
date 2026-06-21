"""Roster (organizer attendance view) schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.enums import RegistrationStatus


class RosterEntry(BaseModel):
    registration_id: UUID
    player_user_id: UUID
    player_display_name: str
    player_email: str
    status: RegistrationStatus
    queue_position: int | None
    assigned_slot_number: int | None
    assigned_arrival_time: datetime | None
    estimated_play_time: datetime | None
    checked_in_at: datetime | None


class RosterResponse(BaseModel):
    run_id: UUID
    confirmed: list[RosterEntry]
    waitlist: list[RosterEntry]
    no_show: list[RosterEntry]
