"""Roster + attendance endpoints (organizer/admin; see docs/API.md)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, get_current_user
from app.db.session import get_db
from app.schemas.registration import RegistrationRead
from app.schemas.roster import RosterResponse
from app.services.roster import RosterService

router = APIRouter(tags=["roster"])


@router.get("/runs/{run_id}/roster", response_model=RosterResponse)
async def get_roster(
    run_id: UUID,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RosterResponse:
    return await RosterService(db).get_roster(run_id, current)


@router.post(
    "/runs/{run_id}/registrations/{registration_id}/check-in",
    response_model=RegistrationRead,
)
async def check_in(
    run_id: UUID,
    registration_id: UUID,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RegistrationRead:
    registration = await RosterService(db).check_in(run_id, registration_id, current)
    return RegistrationRead.model_validate(registration)


@router.post(
    "/runs/{run_id}/registrations/{registration_id}/no-show",
    response_model=RegistrationRead,
)
async def mark_no_show(
    run_id: UUID,
    registration_id: UUID,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RegistrationRead:
    registration = await RosterService(db).mark_no_show(run_id, registration_id, current)
    return RegistrationRead.model_validate(registration)
