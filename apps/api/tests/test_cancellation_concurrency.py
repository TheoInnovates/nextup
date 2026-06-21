"""Concurrent cancellation + promotion — atomicity under the run-row lock.

Two confirmed players cancel at the same time while one waitlister is queued.
The cancellations serialise on the run-row lock, so the waitlister is promoted
exactly once and capacity is never violated (deterministic final state: a single
confirmed player, whoever was promoted).
"""

from __future__ import annotations

import asyncio
import os
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from app.core.dependencies import CurrentUser
from app.db.base import Base
from app.enums import RegistrationStatus, RunStatus, UserRole
from app.models.gym import Gym
from app.models.registration import RunRegistration
from app.models.run import BasketballRun
from app.models.user import UserProfile
from app.services.cancellation import CancellationService
from app.services.registration import RegistrationService
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

_URL = os.environ.get("TEST_DATABASE_URL")


def _engine():
    if not _URL:
        pytest.skip("TEST_DATABASE_URL is not set (a real Postgres is required).")
    return create_async_engine(_URL, poolclass=NullPool)


async def _truncate(engine) -> None:
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "TRUNCATE run_registration, notification, audit_event, "
                "basketball_run, court, gym, user_profile RESTART IDENTITY CASCADE"
            )
        )


async def _seed(engine) -> tuple[UUID, list[UUID]]:
    now = datetime.now(UTC)
    start = now + timedelta(hours=3)
    async with AsyncSession(engine, expire_on_commit=False) as s:
        owner = UserProfile(
            identity_provider_id="cx-owner",
            email="cx-owner@example.com",
            display_name="O",
            default_role=UserRole.organizer,
        )
        s.add(owner)
        await s.flush()
        gym = Gym(
            name="CX Gym",
            description="",
            address_line_1="1",
            city="C",
            state="S",
            postal_code="0",
            timezone="UTC",
            owner_user_id=owner.id,
        )
        s.add(gym)
        await s.flush()
        run = BasketballRun(
            gym_id=gym.id,
            organizer_user_id=owner.id,
            title="CX Run",
            description=None,
            start_time=start,
            end_time=start + timedelta(hours=2),
            registration_opens_at=now - timedelta(days=1),
            registration_closes_at=now + timedelta(hours=1),
            cancellation_deadline=now + timedelta(minutes=30),
            maximum_players=2,
            players_per_team=5,
            number_of_courts=1,
            estimated_game_minutes=12,
            arrival_lead_minutes=10,
            status=RunStatus.published,
        )
        s.add(run)
        await s.flush()
        players = [
            UserProfile(
                identity_provider_id=f"cx-{name}",
                email=f"cx-{name}@example.com",
                display_name=name,
                default_role=UserRole.player,
            )
            for name in ("a", "b", "c")
        ]
        s.add_all(players)
        await s.commit()
        player_ids = [p.id for p in players]
        run_id = run.id

    # Register sequentially: a,b confirmed; c waitlisted.
    async with AsyncSession(engine, expire_on_commit=False) as s:
        service = RegistrationService(s)
        for pid in player_ids:
            await service.register(run_id, pid)
    return run_id, player_ids


async def test_concurrent_cancellations_keep_capacity_invariant() -> None:
    engine = _engine()
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await _truncate(engine)
        run_id, (pa, pb, pc) = await _seed(engine)
        try:

            async def cancel(player_id: UUID) -> None:
                async with AsyncSession(engine, expire_on_commit=False) as session:
                    actor = CurrentUser(profile=UserProfile(id=player_id), roles=["player"])
                    await CancellationService(session).cancel_own(run_id, actor)

            # Cancel both originally-confirmed players at once.
            await asyncio.gather(cancel(pa), cancel(pb))

            async with AsyncSession(engine) as session:
                confirmed = await session.scalar(
                    select(func.count()).where(
                        RunRegistration.run_id == run_id,
                        RunRegistration.status == RegistrationStatus.confirmed,
                    )
                )
                # The waitlister (c) ends up the single confirmed player.
                c_status = await session.scalar(
                    select(RunRegistration.status).where(
                        RunRegistration.run_id == run_id,
                        RunRegistration.player_user_id == pc,
                        RunRegistration.status == RegistrationStatus.confirmed,
                    )
                )
            assert confirmed == 1, confirmed
            assert c_status == RegistrationStatus.confirmed
        finally:
            await _truncate(engine)
    finally:
        await engine.dispose()
