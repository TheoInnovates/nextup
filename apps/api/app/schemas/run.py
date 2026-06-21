"""BasketballRun request/response schemas.

All timestamps must be timezone-aware and are normalised to UTC. Field-level
constraints (422) cover types/ranges; cross-field time-window ordering is checked
for creates here and re-checked after merge in the service for updates.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.enums import RunStatus

_DT_FIELDS = (
    "start_time",
    "end_time",
    "registration_opens_at",
    "registration_closes_at",
    "cancellation_deadline",
)


def _to_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware (include an offset)")
    return value.astimezone(UTC)


def validate_time_window(
    *,
    start_time: datetime,
    end_time: datetime,
    registration_opens_at: datetime,
    registration_closes_at: datetime,
    cancellation_deadline: datetime,
) -> list[str]:
    """Return a list of human-readable ordering problems (empty == valid)."""
    errors: list[str] = []
    if registration_opens_at >= registration_closes_at:
        errors.append("registration_opens_at must be before registration_closes_at")
    if registration_closes_at > start_time:
        errors.append("registration_closes_at must be at or before start_time")
    if start_time >= end_time:
        errors.append("start_time must be before end_time")
    if cancellation_deadline > start_time:
        errors.append("cancellation_deadline must be at or before start_time")
    return errors


class RunBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    start_time: datetime
    end_time: datetime
    registration_opens_at: datetime
    registration_closes_at: datetime
    cancellation_deadline: datetime
    maximum_players: int = Field(ge=2, le=1000)
    players_per_team: int = Field(ge=1, le=50)
    number_of_courts: int = Field(ge=1, le=50)
    estimated_game_minutes: int = Field(ge=1, le=600)
    arrival_lead_minutes: int = Field(ge=0, le=240)

    @field_validator(*_DT_FIELDS)
    @classmethod
    def _aware_utc(cls, value: datetime) -> datetime:
        return _to_utc(value)


class RunCreate(RunBase):
    gym_id: UUID

    @model_validator(mode="after")
    def _check_window(self) -> RunCreate:
        problems = validate_time_window(
            start_time=self.start_time,
            end_time=self.end_time,
            registration_opens_at=self.registration_opens_at,
            registration_closes_at=self.registration_closes_at,
            cancellation_deadline=self.cancellation_deadline,
        )
        if problems:
            raise ValueError("; ".join(problems))
        return self


class RunUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    start_time: datetime | None = None
    end_time: datetime | None = None
    registration_opens_at: datetime | None = None
    registration_closes_at: datetime | None = None
    cancellation_deadline: datetime | None = None
    maximum_players: int | None = Field(default=None, ge=2, le=1000)
    players_per_team: int | None = Field(default=None, ge=1, le=50)
    number_of_courts: int | None = Field(default=None, ge=1, le=50)
    estimated_game_minutes: int | None = Field(default=None, ge=1, le=600)
    arrival_lead_minutes: int | None = Field(default=None, ge=0, le=240)

    @field_validator(*_DT_FIELDS)
    @classmethod
    def _aware_utc(cls, value: datetime | None) -> datetime | None:
        return _to_utc(value) if value is not None else None


class RunRead(RunBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    gym_id: UUID
    organizer_user_id: UUID
    status: RunStatus
    created_at: datetime
    updated_at: datetime
