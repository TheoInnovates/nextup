"""Gym and Court endpoints (see docs/API.md).

GET endpoints require authentication (any role). Creating a gym requires the
organizer (or admin) role; per-object management is authorized in the service
layer by ownership.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, get_current_user, require_role
from app.db.session import get_db
from app.schemas.common import Page
from app.schemas.gym import (
    CourtCreate,
    CourtRead,
    CourtUpdate,
    GymCreate,
    GymRead,
    GymUpdate,
)
from app.services.gym import CourtService, GymService

router = APIRouter(tags=["gyms"])


# --- gyms --------------------------------------------------------------------
@router.get("/gyms", response_model=Page[GymRead])
async def list_gyms(
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> Page[GymRead]:
    items, total = await GymService(db).list(current, limit=limit, offset=offset)
    return Page[GymRead](
        items=[GymRead.model_validate(g) for g in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/gyms", response_model=GymRead, status_code=status.HTTP_201_CREATED)
async def create_gym(
    payload: GymCreate,
    current: CurrentUser = Depends(require_role("organizer", "admin")),
    db: AsyncSession = Depends(get_db),
) -> GymRead:
    gym = await GymService(db).create(payload, current)
    return GymRead.model_validate(gym)


@router.get("/gyms/{gym_id}", response_model=GymRead)
async def get_gym(
    gym_id: UUID,
    _: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GymRead:
    gym = await GymService(db).get(gym_id)
    return GymRead.model_validate(gym)


@router.patch("/gyms/{gym_id}", response_model=GymRead)
async def update_gym(
    gym_id: UUID,
    payload: GymUpdate,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GymRead:
    gym = await GymService(db).update(gym_id, payload, current)
    return GymRead.model_validate(gym)


@router.delete("/gyms/{gym_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_gym(
    gym_id: UUID,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await GymService(db).soft_delete(gym_id, current)


# --- courts ------------------------------------------------------------------
@router.get("/gyms/{gym_id}/courts", response_model=list[CourtRead])
async def list_courts(
    gym_id: UUID,
    _: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[CourtRead]:
    courts = await CourtService(db).list_for_gym(gym_id)
    return [CourtRead.model_validate(c) for c in courts]


@router.post(
    "/gyms/{gym_id}/courts",
    response_model=CourtRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_court(
    gym_id: UUID,
    payload: CourtCreate,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CourtRead:
    court = await CourtService(db).create(gym_id, payload, current)
    return CourtRead.model_validate(court)


@router.patch("/courts/{court_id}", response_model=CourtRead)
async def update_court(
    court_id: UUID,
    payload: CourtUpdate,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CourtRead:
    court = await CourtService(db).update(court_id, payload, current)
    return CourtRead.model_validate(court)


@router.delete("/courts/{court_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_court(
    court_id: UUID,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await CourtService(db).soft_delete(court_id, current)
