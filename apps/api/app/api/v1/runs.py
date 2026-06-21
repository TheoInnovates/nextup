"""BasketballRun endpoints (see docs/API.md).

Listing/detail require authentication (any role); players never see drafts.
Creating requires organizer/admin; per-run management (edit, lifecycle
transitions) is authorized by ownership in the service.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, get_current_user, require_role
from app.db.session import get_db
from app.enums import RunStatus
from app.schemas.common import Page
from app.schemas.run import RunCreate, RunRead, RunUpdate
from app.services.run import RunService

router = APIRouter(tags=["runs"])


@router.get("/runs", response_model=Page[RunRead])
async def list_runs(
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    gym_id: UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> Page[RunRead]:
    items, total = await RunService(db).list(current, gym_id=gym_id, limit=limit, offset=offset)
    return Page[RunRead](
        items=[RunRead.model_validate(r) for r in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/runs", response_model=RunRead, status_code=status.HTTP_201_CREATED)
async def create_run(
    payload: RunCreate,
    current: CurrentUser = Depends(require_role("organizer", "admin")),
    db: AsyncSession = Depends(get_db),
) -> RunRead:
    run = await RunService(db).create(payload, current)
    return RunRead.model_validate(run)


@router.get("/runs/{run_id}", response_model=RunRead)
async def get_run(
    run_id: UUID,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RunRead:
    run = await RunService(db).get_for_view(run_id, current)
    return RunRead.model_validate(run)


@router.patch("/runs/{run_id}", response_model=RunRead)
async def update_run(
    run_id: UUID,
    payload: RunUpdate,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RunRead:
    run = await RunService(db).update(run_id, payload, current)
    return RunRead.model_validate(run)


@router.delete("/runs/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_run(
    run_id: UUID,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    # "Soft-disable" a run == cancel it (runs are never hard-deleted).
    await RunService(db).transition(run_id, RunStatus.cancelled, current)


@router.post("/runs/{run_id}/publish", response_model=RunRead)
async def publish_run(
    run_id: UUID,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RunRead:
    run = await RunService(db).transition(run_id, RunStatus.published, current)
    return RunRead.model_validate(run)


@router.post("/runs/{run_id}/cancel", response_model=RunRead)
async def cancel_run(
    run_id: UUID,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RunRead:
    run = await RunService(db).transition(run_id, RunStatus.cancelled, current)
    return RunRead.model_validate(run)


@router.post("/runs/{run_id}/start", response_model=RunRead)
async def start_run(
    run_id: UUID,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RunRead:
    run = await RunService(db).transition(run_id, RunStatus.in_progress, current)
    return RunRead.model_validate(run)


@router.post("/runs/{run_id}/complete", response_model=RunRead)
async def complete_run(
    run_id: UUID,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RunRead:
    run = await RunService(db).transition(run_id, RunStatus.completed, current)
    return RunRead.model_validate(run)
