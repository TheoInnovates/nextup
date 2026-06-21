"""Notification endpoints (see docs/API.md)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, get_current_user
from app.db.session import get_db
from app.schemas.common import Page
from app.schemas.notification import NotificationRead
from app.services.notification import NotificationService

router = APIRouter(tags=["notifications"])


@router.get("/notifications", response_model=Page[NotificationRead])
async def list_notifications(
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> Page[NotificationRead]:
    items, total = await NotificationService(db).list_for_user(
        current.id, limit=limit, offset=offset
    )
    return Page[NotificationRead](
        items=[NotificationRead.model_validate(n) for n in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/notifications/{notification_id}/read", response_model=NotificationRead)
async def mark_notification_read(
    notification_id: UUID,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationRead:
    notification = await NotificationService(db).mark_read(notification_id, current.id)
    return NotificationRead.model_validate(notification)


@router.post("/notifications/read-all", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_notifications_read(
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await NotificationService(db).mark_all_read(current.id)
