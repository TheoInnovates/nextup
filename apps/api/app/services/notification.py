"""In-app notification logic."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.enums import NotificationType
from app.models.notification import Notification
from app.repositories.notification import NotificationRepository


class NotificationService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = NotificationRepository(db)

    async def create(
        self,
        *,
        user_id: UUID,
        type: NotificationType,
        title: str,
        message: str,
        related_run_id: UUID | None = None,
    ) -> Notification:
        """Create a notification (flush only — the caller owns the transaction)."""
        notification = Notification(
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            related_run_id=related_run_id,
        )
        return await self.repo.add(notification)

    async def list_for_user(
        self, user_id: UUID, *, limit: int, offset: int
    ) -> tuple[list[Notification], int]:
        return await self.repo.list_for_user(user_id, limit=limit, offset=offset)

    async def mark_read(self, notification_id: UUID, user_id: UUID) -> Notification:
        notification = await self.repo.get_by_id(notification_id)
        if notification is None or notification.user_id != user_id:
            raise NotFoundError("Notification not found.")
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.now(UTC)
        await self.db.commit()
        await self.db.refresh(notification)
        return notification

    async def mark_all_read(self, user_id: UUID) -> None:
        await self.repo.mark_all_read(user_id)
        await self.db.commit()
