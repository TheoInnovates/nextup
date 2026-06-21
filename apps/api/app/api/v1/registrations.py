"""Registration endpoints (see docs/API.md).

A player registers themselves for a run; the response carries confirmed/waitlist
status plus the computed arrival and play times. Conflicts (duplicate, closed
registration, lost final-slot race) return 409.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, get_current_user, require_role
from app.core.ratelimit import registration_rate_limit
from app.db.session import get_db
from app.schemas.registration import RegistrationRead
from app.services.cancellation import CancellationService
from app.services.registration import RegistrationService

router = APIRouter(tags=["registrations"])


@router.post(
    "/runs/{run_id}/registrations",
    response_model=RegistrationRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(registration_rate_limit)],
)
async def register_for_run(
    run_id: UUID,
    current: CurrentUser = Depends(require_role("player")),
    db: AsyncSession = Depends(get_db),
) -> RegistrationRead:
    registration = await RegistrationService(db).register(run_id, current.id)
    return RegistrationRead.model_validate(registration)


@router.get(
    "/runs/{run_id}/registrations/me",
    response_model=RegistrationRead,
)
async def get_my_registration(
    run_id: UUID,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RegistrationRead:
    registration = await RegistrationService(db).get_for_player(run_id, current.id)
    return RegistrationRead.model_validate(registration)


@router.delete(
    "/runs/{run_id}/registrations/me",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def cancel_my_registration(
    run_id: UUID,
    current: CurrentUser = Depends(require_role("player")),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Cancel the caller's registration; triggers waitlist promotion."""
    await CancellationService(db).cancel_own(run_id, current)


@router.delete(
    "/runs/{run_id}/registrations/{registration_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def cancel_registration(
    run_id: UUID,
    registration_id: UUID,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Organizer/admin cancels a player's registration; triggers promotion."""
    await CancellationService(db).cancel_registration(run_id, registration_id, current)


@router.post(
    "/runs/{run_id}/registrations/{registration_id}/promote",
    response_model=RegistrationRead,
)
async def promote_registration(
    run_id: UUID,
    registration_id: UUID,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RegistrationRead:
    """Manually promote a waitlisted registration (organizer/admin)."""
    registration = await CancellationService(db).promote_manual(run_id, registration_id, current)
    return RegistrationRead.model_validate(registration)
