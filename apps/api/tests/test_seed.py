"""Seed-data tests (creation + idempotency)."""

from __future__ import annotations

from app.enums import RegistrationStatus
from app.models.gym import Gym
from app.models.registration import RunRegistration
from app.models.user import UserProfile
from app.seed import GYM_ID, RUN_FULL, seed
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


async def test_seed_creates_expected_data(db_session: AsyncSession) -> None:
    await seed(db_session)

    assert await db_session.get(Gym, GYM_ID) is not None
    users = await db_session.scalar(select(func.count()).select_from(UserProfile))
    assert users == 5

    confirmed = await db_session.scalar(
        select(func.count()).where(
            RunRegistration.run_id == RUN_FULL,
            RunRegistration.status == RegistrationStatus.confirmed,
        )
    )
    waitlisted = await db_session.scalar(
        select(func.count()).where(
            RunRegistration.run_id == RUN_FULL,
            RunRegistration.status == RegistrationStatus.waitlisted,
        )
    )
    assert confirmed == 2
    assert waitlisted == 1


async def test_seed_is_idempotent(db_session: AsyncSession) -> None:
    await seed(db_session)
    await seed(db_session)
    gyms = await db_session.scalar(select(func.count()).select_from(Gym))
    registrations = await db_session.scalar(select(func.count()).select_from(RunRegistration))
    assert gyms == 1
    assert registrations == 3  # no duplicates on the second run
