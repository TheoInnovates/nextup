"""Final-slot race test — genuinely concurrent transactions (no mocking).

Two players race for the last confirmed slot. The run-row ``SELECT … FOR UPDATE``
lock must serialise them so exactly one is confirmed and the other waitlisted.

This test deliberately bypasses the savepoint-rollback ``db_session`` fixture: it
needs real concurrent connections that COMMIT. It uses its own engine and cleans
up with ``TRUNCATE`` in ``finally`` so the committed rows never leak into the
rollback-isolated tests.

Self-proving: with the ``with_for_update`` lock removed from
``RegistrationService.register``, both transactions read ``occupying == 0`` and
both confirm — this test then fails with two ``confirmed`` (verified manually
during development).
"""

from __future__ import annotations

import asyncio
import os
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from app.db.base import Base
from app.enums import RegistrationStatus, RunStatus, UserRole
from app.models.gym import Gym
from app.models.registration import RunRegistration
from app.models.run import BasketballRun
from app.models.user import UserProfile
from app.services.registration import RegistrationService
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

_URL = os.environ.get("TEST_DATABASE_URL")


def _engine():
    if not _URL:
        pytest.skip("TEST_DATABASE_URL is not set (a real Postgres is required).")
    return create_async_engine(_URL, poolclass=NullPool)


async def _seed(engine, *, maximum_players: int) -> tuple[UUID, UUID, UUID]:
    now = datetime.now(UTC)
    start = now + timedelta(hours=3)
    async with AsyncSession(engine, expire_on_commit=False) as s:
        owner = UserProfile(
            identity_provider_id="race-owner",
            email="race-owner@example.com",
            display_name="Owner",
            default_role=UserRole.organizer,
        )
        s.add(owner)
        await s.flush()
        gym = Gym(
            name="Race Gym",
            description="",
            address_line_1="1 Court St",
            city="Boston",
            state="MA",
            postal_code="02108",
            timezone="UTC",
            owner_user_id=owner.id,
        )
        s.add(gym)
        await s.flush()
        run = BasketballRun(
            gym_id=gym.id,
            organizer_user_id=owner.id,
            title="Race Run",
            description=None,
            start_time=start,
            end_time=start + timedelta(hours=2),
            registration_opens_at=now - timedelta(days=1),
            registration_closes_at=now + timedelta(hours=1),
            cancellation_deadline=now + timedelta(minutes=30),
            maximum_players=maximum_players,
            players_per_team=5,
            number_of_courts=1,
            estimated_game_minutes=12,
            arrival_lead_minutes=10,
            status=RunStatus.published,
        )
        s.add(run)
        await s.flush()
        player_a = UserProfile(
            identity_provider_id="race-a",
            email="race-a@example.com",
            display_name="A",
            default_role=UserRole.player,
        )
        player_b = UserProfile(
            identity_provider_id="race-b",
            email="race-b@example.com",
            display_name="B",
            default_role=UserRole.player,
        )
        s.add_all([player_a, player_b])
        await s.commit()
        return run.id, player_a.id, player_b.id


async def _truncate(engine) -> None:
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "TRUNCATE run_registration, basketball_run, court, gym, "
                "user_profile RESTART IDENTITY CASCADE"
            )
        )


async def test_final_slot_race_serialised() -> None:
    engine = _engine()
    try:
        # Ensure schema exists regardless of test ordering (idempotent).
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await _truncate(engine)
        run_id, player_a, player_b = await _seed(engine, maximum_players=1)
        try:

            async def register(player_id: UUID) -> RegistrationStatus:
                async with AsyncSession(engine, expire_on_commit=False) as session:
                    reg = await RegistrationService(session).register(run_id, player_id)
                    return reg.status

            results = await asyncio.gather(register(player_a), register(player_b))
            statuses = sorted(status.value for status in results)
            assert statuses == ["confirmed", "waitlisted"], statuses

            async with AsyncSession(engine) as session:
                confirmed = await session.scalar(
                    select(func.count()).where(
                        RunRegistration.run_id == run_id,
                        RunRegistration.status == RegistrationStatus.confirmed,
                    )
                )
                active = await session.scalar(
                    select(func.count()).where(
                        RunRegistration.run_id == run_id,
                        RunRegistration.status.in_(
                            [RegistrationStatus.confirmed, RegistrationStatus.waitlisted]
                        ),
                    )
                )
            assert confirmed == 1
            assert active == 2
        finally:
            await _truncate(engine)
    finally:
        await engine.dispose()
