"""Data access for RunRegistration."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import RegistrationStatus
from app.models.registration import RunRegistration

# Statuses that occupy a confirmed slot for capacity counting.
OCCUPYING_STATUSES = (RegistrationStatus.confirmed, RegistrationStatus.checked_in)
ACTIVE_STATUSES = (
    RegistrationStatus.confirmed,
    RegistrationStatus.waitlisted,
    RegistrationStatus.checked_in,
)


class RegistrationRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def add(self, registration: RunRegistration) -> RunRegistration:
        self.db.add(registration)
        await self.db.flush()
        return registration

    async def get_active_for_player(
        self, run_id: UUID, player_user_id: UUID
    ) -> RunRegistration | None:
        stmt = select(RunRegistration).where(
            RunRegistration.run_id == run_id,
            RunRegistration.player_user_id == player_user_id,
            RunRegistration.status.in_(ACTIVE_STATUSES),
        )
        return await self.db.scalar(stmt)

    async def count_occupying(self, run_id: UUID) -> int:
        stmt = select(func.count()).where(
            RunRegistration.run_id == run_id,
            RunRegistration.status.in_(OCCUPYING_STATUSES),
        )
        return await self.db.scalar(stmt) or 0

    async def count_waitlisted(self, run_id: UUID) -> int:
        stmt = select(func.count()).where(
            RunRegistration.run_id == run_id,
            RunRegistration.status == RegistrationStatus.waitlisted,
        )
        return await self.db.scalar(stmt) or 0

    async def get_by_id(self, registration_id: UUID) -> RunRegistration | None:
        return await self.db.get(RunRegistration, registration_id)

    async def list_occupying_ordered(self, run_id: UUID) -> list[RunRegistration]:
        """Confirmed + checked-in registrations, deterministically ordered."""
        stmt = (
            select(RunRegistration)
            .where(
                RunRegistration.run_id == run_id,
                RunRegistration.status.in_(OCCUPYING_STATUSES),
            )
            .order_by(RunRegistration.registered_at.asc(), RunRegistration.id.asc())
        )
        return list(await self.db.scalars(stmt))

    async def list_waitlisted_ordered(self, run_id: UUID) -> list[RunRegistration]:
        stmt = (
            select(RunRegistration)
            .where(
                RunRegistration.run_id == run_id,
                RunRegistration.status == RegistrationStatus.waitlisted,
            )
            .order_by(RunRegistration.registered_at.asc(), RunRegistration.id.asc())
        )
        return list(await self.db.scalars(stmt))

    async def list_for_run(self, run_id: UUID) -> list[RunRegistration]:
        """All registrations for a run (roster view), active first by time."""
        stmt = (
            select(RunRegistration)
            .where(RunRegistration.run_id == run_id)
            .order_by(RunRegistration.registered_at.asc(), RunRegistration.id.asc())
        )
        return list(await self.db.scalars(stmt))
