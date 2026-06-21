"""Gym and Court business logic, including object-level authorization.

Ownership is enforced here (not in handlers): an organizer may modify only gyms
they own; admins override. Missing resources raise 404; existing-but-not-owned
resources raise 403 (see docs/API.md status codes).
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser
from app.core.exceptions import AuthorizationError, NotFoundError
from app.enums import UserRole
from app.models.gym import Court, Gym
from app.repositories.gym import CourtRepository, GymRepository
from app.schemas.gym import CourtCreate, CourtUpdate, GymCreate, GymUpdate


def _assert_can_manage(gym: Gym, user: CurrentUser) -> None:
    if user.has_role(UserRole.admin):
        return
    if gym.owner_user_id == user.id:
        return
    raise AuthorizationError("You do not own this gym.")


class GymService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = GymRepository(db)

    async def create(self, data: GymCreate, owner: CurrentUser) -> Gym:
        gym = Gym(**data.model_dump(), owner_user_id=owner.id)
        await self.repo.add(gym)
        await self.db.commit()
        await self.db.refresh(gym)
        return gym

    async def get(self, gym_id: UUID) -> Gym:
        gym = await self.repo.get(gym_id)
        if gym is None:
            raise NotFoundError("Gym not found.")
        return gym

    async def list(self, viewer: CurrentUser, *, limit: int, offset: int) -> tuple[list[Gym], int]:
        return await self.repo.list_visible(
            viewer_id=viewer.id,
            is_admin=viewer.has_role(UserRole.admin),
            limit=limit,
            offset=offset,
        )

    async def update(self, gym_id: UUID, data: GymUpdate, user: CurrentUser) -> Gym:
        gym = await self.get(gym_id)
        _assert_can_manage(gym, user)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(gym, field, value)
        await self.db.commit()
        await self.db.refresh(gym)
        return gym

    async def soft_delete(self, gym_id: UUID, user: CurrentUser) -> None:
        gym = await self.get(gym_id)
        _assert_can_manage(gym, user)
        gym.is_active = False
        await self.db.commit()


class CourtService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = CourtRepository(db)
        self.gym_repo = GymRepository(db)

    async def _load_gym(self, gym_id: UUID) -> Gym:
        gym = await self.gym_repo.get(gym_id)
        if gym is None:
            raise NotFoundError("Gym not found.")
        return gym

    async def _load_court(self, court_id: UUID) -> tuple[Court, Gym]:
        court = await self.repo.get(court_id)
        if court is None:
            raise NotFoundError("Court not found.")
        gym = await self._load_gym(court.gym_id)
        return court, gym

    async def list_for_gym(self, gym_id: UUID) -> list[Court]:
        await self._load_gym(gym_id)
        return await self.repo.list_for_gym(gym_id)

    async def create(self, gym_id: UUID, data: CourtCreate, user: CurrentUser) -> Court:
        gym = await self._load_gym(gym_id)
        _assert_can_manage(gym, user)
        court = Court(gym_id=gym.id, **data.model_dump())
        await self.repo.add(court)
        await self.db.commit()
        await self.db.refresh(court)
        return court

    async def update(self, court_id: UUID, data: CourtUpdate, user: CurrentUser) -> Court:
        court, gym = await self._load_court(court_id)
        _assert_can_manage(gym, user)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(court, field, value)
        await self.db.commit()
        await self.db.refresh(court)
        return court

    async def soft_delete(self, court_id: UUID, user: CurrentUser) -> None:
        court, gym = await self._load_court(court_id)
        _assert_can_manage(gym, user)
        court.is_active = False
        await self.db.commit()
