"""Registration response schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.enums import RegistrationStatus


class RegistrationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    run_id: UUID
    player_user_id: UUID
    status: RegistrationStatus
    queue_position: int | None
    assigned_slot_number: int | None
    assigned_arrival_time: datetime | None
    estimated_play_time: datetime | None
    registered_at: datetime
    cancelled_at: datetime | None
    checked_in_at: datetime | None
