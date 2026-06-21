"""Idempotent development seed data (spec §19).

Run with ``python -m app.seed`` (``make seed``). Entity IDs are fixed so the seed
is idempotent, and the user IDs match the Keycloak realm user IDs so that when a
seeded user logs in, claim-sync matches the existing profile (no duplicate).

Creates: admin + organizer + 3 players, a gym with 2 courts, and three runs —
a draft, an open published run, and a full published run (2 confirmed + 1
waitlisted) demonstrating the waitlist.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import configure_logging, get_logger
from app.db.session import engine
from app.enums import RegistrationStatus, RunStatus, UserRole
from app.models.gym import Court, Gym
from app.models.registration import RunRegistration
from app.models.run import BasketballRun
from app.models.user import UserProfile
from app.scheduling.engine import compute_assignment
from app.services.registration import build_scheduling_params

log = get_logger("app.seed")

ADMIN_ID = UUID("11111111-1111-1111-1111-111111111111")
ORG_ID = UUID("22222222-2222-2222-2222-222222222222")
P1 = UUID("33333333-3333-3333-3333-333333333333")
P2 = UUID("44444444-4444-4444-4444-444444444444")
P3 = UUID("55555555-5555-5555-5555-555555555555")
GYM_ID = UUID("aaaaaaaa-0000-0000-0000-000000000001")
COURT_A = UUID("aaaaaaaa-0000-0000-0000-0000000000ca")
COURT_B = UUID("aaaaaaaa-0000-0000-0000-0000000000cb")
RUN_OPEN = UUID("bbbbbbbb-0000-0000-0000-000000000001")
RUN_FULL = UUID("bbbbbbbb-0000-0000-0000-000000000002")
RUN_DRAFT = UUID("bbbbbbbb-0000-0000-0000-000000000003")

_USERS = [
    (ADMIN_ID, "admin1@nextup.local", "Adah Admin", UserRole.admin),
    (ORG_ID, "organizer1@nextup.local", "Olive Organizer", UserRole.organizer),
    (P1, "player1@nextup.local", "Penny Player", UserRole.player),
    (P2, "player2@nextup.local", "Pablo Player", UserRole.player),
    (P3, "player3@nextup.local", "Priya Player", UserRole.player),
]


async def _get_or_create[T](session: AsyncSession, model: type[T], pk: UUID, instance: T) -> T:
    """Return the row with ``pk`` if present, else persist ``instance``.

    ``instance`` is built eagerly by the caller (cheap, and avoids generic-lambda
    type-inference issues); it is simply discarded if the row already exists.
    """
    existing = await session.get(model, pk)
    if existing is not None:
        return existing
    session.add(instance)
    await session.flush()
    return instance


def _run(
    run_id: UUID,
    title: str,
    *,
    status: RunStatus,
    start: datetime,
    now: datetime,
    maximum_players: int,
    number_of_courts: int,
) -> BasketballRun:
    return BasketballRun(
        id=run_id,
        gym_id=GYM_ID,
        organizer_user_id=ORG_ID,
        title=title,
        description="Seeded demo run.",
        start_time=start,
        end_time=start + timedelta(hours=2),
        registration_opens_at=now - timedelta(hours=1),
        registration_closes_at=start - timedelta(hours=1),
        cancellation_deadline=start - timedelta(hours=2),
        maximum_players=maximum_players,
        players_per_team=5,
        number_of_courts=number_of_courts,
        estimated_game_minutes=12,
        arrival_lead_minutes=15,
        status=status,
    )


async def seed(session: AsyncSession) -> None:
    now = datetime.now(UTC)

    for uid, email, name, role in _USERS:
        await _get_or_create(
            session,
            UserProfile,
            uid,
            UserProfile(
                id=uid,
                identity_provider_id=str(uid),
                email=email,
                display_name=name,
                default_role=role,
            ),
        )

    await _get_or_create(
        session,
        Gym,
        GYM_ID,
        Gym(
            id=GYM_ID,
            name="Downtown Rec Center",
            description="Two full courts downtown.",
            address_line_1="100 Main St",
            city="Boston",
            state="MA",
            postal_code="02108",
            timezone="America/New_York",
            owner_user_id=ORG_ID,
        ),
    )
    await _get_or_create(session, Court, COURT_A, Court(id=COURT_A, gym_id=GYM_ID, name="Court A"))
    await _get_or_create(session, Court, COURT_B, Court(id=COURT_B, gym_id=GYM_ID, name="Court B"))

    await _get_or_create(
        session,
        BasketballRun,
        RUN_DRAFT,
        _run(
            RUN_DRAFT,
            "Draft: Sunday Skills",
            status=RunStatus.draft,
            start=now + timedelta(days=5),
            now=now,
            maximum_players=20,
            number_of_courts=2,
        ),
    )
    await _get_or_create(
        session,
        BasketballRun,
        RUN_OPEN,
        _run(
            RUN_OPEN,
            "Tuesday Night Run",
            status=RunStatus.published,
            start=now + timedelta(days=2),
            now=now,
            maximum_players=20,
            number_of_courts=2,
        ),
    )

    full = await session.get(BasketballRun, RUN_FULL)
    if full is None:
        full = _run(
            RUN_FULL,
            "Sold-out Saturday",
            status=RunStatus.published,
            start=now + timedelta(days=3),
            now=now,
            maximum_players=2,
            number_of_courts=1,
        )
        session.add(full)
        await session.flush()
        params = build_scheduling_params(full)
        for position, player_id in enumerate((P1, P2)):
            assignment = compute_assignment(params, position)
            session.add(
                RunRegistration(
                    run_id=RUN_FULL,
                    player_user_id=player_id,
                    status=RegistrationStatus.confirmed,
                    assigned_slot_number=assignment.slot_number,
                    estimated_play_time=assignment.estimated_play_time,
                    assigned_arrival_time=assignment.assigned_arrival_time,
                    registered_at=now + timedelta(seconds=position),
                )
            )
        session.add(
            RunRegistration(
                run_id=RUN_FULL,
                player_user_id=P3,
                status=RegistrationStatus.waitlisted,
                queue_position=1,
                registered_at=now + timedelta(seconds=2),
            )
        )

    await session.commit()
    log.info("seed.complete")


async def main() -> None:
    # Requires an already-migrated schema (run `make migrate` first) — we don't
    # create_all here, to avoid producing tables with no alembic_version.
    configure_logging()
    async with AsyncSession(engine, expire_on_commit=False) as session:
        await seed(session)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
