"""Current-user endpoints: GET/PATCH /me."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser, get_current_user
from app.db.session import get_db
from app.schemas.user import UserRead, UserUpdate
from app.services.user import UserService

router = APIRouter(tags=["users"])


def _to_read(current: CurrentUser) -> UserRead:
    model = UserRead.model_validate(current.profile)
    return model.model_copy(update={"roles": current.roles})


@router.get("/me", response_model=UserRead)
async def read_me(current: CurrentUser = Depends(get_current_user)) -> UserRead:
    return _to_read(current)


@router.patch("/me", response_model=UserRead)
async def update_me(
    payload: UserUpdate,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    updated = await UserService(db).update_profile(current.profile, payload)
    await db.commit()
    return _to_read(CurrentUser(profile=updated, roles=current.roles))
