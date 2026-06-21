"""Data access for BasketballRun."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import RunStatus
from app.models.run import BasketballRun


class RunRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get(self, run_id: UUID) -> BasketballRun | None:
        return await self.db.get(BasketballRun, run_id)

    async def add(self, run: BasketballRun) -> BasketballRun:
        self.db.add(run)
        await self.db.flush()
        return run

    async def list_visible(
        self,
        *,
        viewer_id: UUID,
        is_admin: bool,
        gym_id: UUID | None,
        limit: int,
        offset: int,
    ) -> tuple[list[BasketballRun], int]:
        """Non-admins see published+ runs plus any runs they organize (incl. drafts)."""
        stmt = select(BasketballRun)
        if gym_id is not None:
            stmt = stmt.where(BasketballRun.gym_id == gym_id)
        if not is_admin:
            stmt = stmt.where(
                or_(
                    BasketballRun.status != RunStatus.draft,
                    BasketballRun.organizer_user_id == viewer_id,
                )
            )
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await self.db.scalar(count_stmt) or 0
        page_stmt = stmt.order_by(BasketballRun.start_time.asc()).limit(limit).offset(offset)
        rows = list(await self.db.scalars(page_stmt))
        return rows, total
