"""Gym and Court request/response schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _validate_timezone(value: str) -> str:
    try:
        ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ValueError(f"Unknown IANA timezone: {value!r}") from exc
    return value


class GymBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    address_line_1: str = Field(min_length=1, max_length=200)
    address_line_2: str | None = Field(default=None, max_length=200)
    city: str = Field(min_length=1, max_length=120)
    state: str = Field(min_length=1, max_length=120)
    postal_code: str = Field(min_length=1, max_length=20)
    timezone: str = Field(description="IANA timezone, e.g. America/New_York")

    _check_tz = field_validator("timezone")(_validate_timezone)


class GymCreate(GymBase):
    pass


class GymUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    address_line_1: str | None = Field(default=None, min_length=1, max_length=200)
    address_line_2: str | None = Field(default=None, max_length=200)
    city: str | None = Field(default=None, min_length=1, max_length=120)
    state: str | None = Field(default=None, min_length=1, max_length=120)
    postal_code: str | None = Field(default=None, min_length=1, max_length=20)
    timezone: str | None = Field(default=None)
    is_active: bool | None = None

    @field_validator("timezone")
    @classmethod
    def _check_tz(cls, value: str | None) -> str | None:
        return _validate_timezone(value) if value is not None else None


class GymRead(GymBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owner_user_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CourtBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class CourtCreate(CourtBase):
    pass


class CourtUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    is_active: bool | None = None


class CourtRead(CourtBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    gym_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
