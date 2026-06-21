"""Data access for Notification."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification


class NotificationRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def add(self, notification: Notification) -> Notification:
        self.db.add(notification)
        await self.db.flush()
        return notification

    async def get_by_id(self, notification_id: UUID) -> Notification | None:
        return await self.db.get(Notification, notification_id)

    async def list_for_user(
        self, user_id: UUID, *, limit: int, offset: int
    ) -> tuple[list[Notification], int]:
        base = select(Notification).where(Notification.user_id == user_id)
        total = await self.db.scalar(select(func.count()).select_from(base.subquery()))
        stmt = base.order_by(Notification.created_at.desc()).limit(limit).offset(offset)
        rows = list(await self.db.scalars(stmt))
        return rows, total or 0

    async def mark_all_read(self, user_id: UUID) -> None:
        stmt = (
            update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read.is_(False))
            .values(is_read=True, read_at=datetime.now(UTC))
        )
        await self.db.execute(stmt)
