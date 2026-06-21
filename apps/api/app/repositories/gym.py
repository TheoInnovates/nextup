"""Data access for Gym and Court."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.gym import Court, Gym


class GymRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get(self, gym_id: UUID) -> Gym | None:
        return await self.db.get(Gym, gym_id)

    async def add(self, gym: Gym) -> Gym:
        self.db.add(gym)
        await self.db.flush()
        return gym

    async def list_visible(
        self, *, viewer_id: UUID, is_admin: bool, limit: int, offset: int
    ) -> tuple[list[Gym], int]:
        """Admins see all gyms; everyone else sees active gyms plus their own."""
        stmt = select(Gym)
        if not is_admin:
            stmt = stmt.where(or_(Gym.is_active.is_(True), Gym.owner_user_id == viewer_id))
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await self.db.scalar(count_stmt) or 0
        page_stmt = stmt.order_by(Gym.created_at.desc()).limit(limit).offset(offset)
        rows = list(await self.db.scalars(page_stmt))
        return rows, total


class CourtRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get(self, court_id: UUID) -> Court | None:
        return await self.db.get(Court, court_id)

    async def add(self, court: Court) -> Court:
        self.db.add(court)
        await self.db.flush()
        return court

    async def list_for_gym(self, gym_id: UUID) -> list[Court]:
        stmt = select(Court).where(Court.gym_id == gym_id).order_by(Court.created_at.asc())
        return list(await self.db.scalars(stmt))
