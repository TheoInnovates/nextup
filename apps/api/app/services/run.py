"""BasketballRun business logic: status machine, visibility, authorization.

The status machine is a pure, separately-tested mapping; invalid transitions
raise 409 (ConflictError). Object-level authorization: a run is managed by its
organizer (or admin). Players never see drafts.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authz import assert_can_manage
from app.core.dependencies import CurrentUser
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.enums import RunStatus, UserRole
from app.models.run import BasketballRun
from app.repositories.gym import GymRepository
from app.repositories.run import RunRepository
from app.schemas.run import RunCreate, RunUpdate, validate_time_window

# --- status machine (pure) ---------------------------------------------------
ALLOWED_TRANSITIONS: dict[RunStatus, set[RunStatus]] = {
    RunStatus.draft: {RunStatus.published, RunStatus.cancelled},
    RunStatus.published: {
        RunStatus.registration_closed,
        RunStatus.in_progress,
        RunStatus.cancelled,
    },
    RunStatus.registration_closed: {RunStatus.in_progress, RunStatus.cancelled},
    RunStatus.in_progress: {RunStatus.completed, RunStatus.cancelled},
    RunStatus.completed: set(),
    RunStatus.cancelled: set(),
}

EDITABLE_STATUSES = {
    RunStatus.draft,
    RunStatus.published,
    RunStatus.registration_closed,
}


def can_transition(current: RunStatus, target: RunStatus) -> bool:
    return target in ALLOWED_TRANSITIONS[current]


def assert_transition(current: RunStatus, target: RunStatus) -> None:
    if not can_transition(current, target):
        raise ConflictError(
            f"Cannot move a run from {current.value} to {target.value}.",
            code="invalid_transition",
        )


# --- service -----------------------------------------------------------------
class RunService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = RunRepository(db)
        self.gym_repo = GymRepository(db)

    async def create(self, data: RunCreate, user: CurrentUser) -> BasketballRun:
        gym = await self.gym_repo.get(data.gym_id)
        if gym is None:
            raise NotFoundError("Gym not found.")
        assert_can_manage(gym.owner_user_id, user, "You do not own this gym.")
        run = BasketballRun(
            **data.model_dump(),
            organizer_user_id=user.id,
            status=RunStatus.draft,
        )
        await self.repo.add(run)
        await self.db.commit()
        await self.db.refresh(run)
        return run

    async def get_for_view(self, run_id: UUID, user: CurrentUser) -> BasketballRun:
        run = await self.repo.get(run_id)
        if run is None:
            raise NotFoundError("Run not found.")
        if run.status == RunStatus.draft and not _is_manager(run, user):
            raise NotFoundError("Run not found.")  # hide drafts from non-managers
        return run

    async def list(
        self, user: CurrentUser, *, gym_id: UUID | None, limit: int, offset: int
    ) -> tuple[list[BasketballRun], int]:
        return await self.repo.list_visible(
            viewer_id=user.id,
            is_admin=user.has_role(UserRole.admin),
            gym_id=gym_id,
            limit=limit,
            offset=offset,
        )

    async def _get_managed(self, run_id: UUID, user: CurrentUser) -> BasketballRun:
        run = await self.repo.get(run_id)
        if run is None:
            raise NotFoundError("Run not found.")
        assert_can_manage(run.organizer_user_id, user, "You do not manage this run.")
        return run

    async def update(self, run_id: UUID, data: RunUpdate, user: CurrentUser) -> BasketballRun:
        run = await self._get_managed(run_id, user)
        if run.status not in EDITABLE_STATUSES:
            raise ConflictError("This run can no longer be edited.", code="not_editable")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(run, field, value)
        problems = validate_time_window(
            start_time=run.start_time,
            end_time=run.end_time,
            registration_opens_at=run.registration_opens_at,
            registration_closes_at=run.registration_closes_at,
            cancellation_deadline=run.cancellation_deadline,
        )
        if problems:
            raise ValidationError("; ".join(problems))
        await self.db.commit()
        await self.db.refresh(run)
        return run

    async def transition(self, run_id: UUID, target: RunStatus, user: CurrentUser) -> BasketballRun:
        run = await self._get_managed(run_id, user)
        assert_transition(run.status, target)
        run.status = target
        await self.db.commit()
        await self.db.refresh(run)
        return run


def _is_manager(run: BasketballRun, user: CurrentUser) -> bool:
    return user.has_role(UserRole.admin) or run.organizer_user_id == user.id
