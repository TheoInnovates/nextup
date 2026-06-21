"""Roster + attendance (check-in / no-show) logic for organizers.

All operations are authorized by run ownership (organizer/admin). Attendance
changes don't alter capacity, so they don't need the run-row lock.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authz import assert_can_manage
from app.core.dependencies import CurrentUser
from app.core.exceptions import ConflictError, NotFoundError
from app.core.metrics import checkins_total
from app.enums import RegistrationStatus
from app.models.registration import RunRegistration
from app.models.run import BasketballRun
from app.models.user import UserProfile
from app.repositories.registration import RegistrationRepository
from app.repositories.run import RunRepository
from app.schemas.roster import RosterEntry, RosterResponse
from app.services.audit import AuditService

_ROSTER_STATUSES = (
    RegistrationStatus.confirmed,
    RegistrationStatus.checked_in,
    RegistrationStatus.waitlisted,
    RegistrationStatus.no_show,
)


def _entry(registration: RunRegistration, user: UserProfile) -> RosterEntry:
    return RosterEntry(
        registration_id=registration.id,
        player_user_id=registration.player_user_id,
        player_display_name=user.display_name,
        player_email=user.email,
        status=registration.status,
        queue_position=registration.queue_position,
        assigned_slot_number=registration.assigned_slot_number,
        assigned_arrival_time=registration.assigned_arrival_time,
        estimated_play_time=registration.estimated_play_time,
        checked_in_at=registration.checked_in_at,
    )


class RosterService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.run_repo = RunRepository(db)
        self.reg_repo = RegistrationRepository(db)
        self.audit = AuditService(db)

    async def _managed_run(self, run_id: UUID, actor: CurrentUser) -> BasketballRun:
        run = await self.run_repo.get(run_id)
        if run is None:
            raise NotFoundError("Run not found.")
        assert_can_manage(run.organizer_user_id, actor, "You do not manage this run.")
        return run

    async def get_roster(self, run_id: UUID, actor: CurrentUser) -> RosterResponse:
        await self._managed_run(run_id, actor)
        stmt = (
            select(RunRegistration, UserProfile)
            .join(UserProfile, RunRegistration.player_user_id == UserProfile.id)
            .where(
                RunRegistration.run_id == run_id,
                RunRegistration.status.in_(_ROSTER_STATUSES),
            )
            .order_by(RunRegistration.registered_at.asc())
        )
        rows = (await self.db.execute(stmt)).all()
        entries = [_entry(reg, user) for reg, user in rows]

        confirmed = sorted(
            (
                e
                for e in entries
                if e.status in (RegistrationStatus.confirmed, RegistrationStatus.checked_in)
            ),
            key=lambda e: e.assigned_slot_number if e.assigned_slot_number is not None else 0,
        )
        waitlist = sorted(
            (e for e in entries if e.status == RegistrationStatus.waitlisted),
            key=lambda e: e.queue_position if e.queue_position is not None else 0,
        )
        no_show = [e for e in entries if e.status == RegistrationStatus.no_show]
        return RosterResponse(
            run_id=run_id, confirmed=confirmed, waitlist=waitlist, no_show=no_show
        )

    async def _load_registration(self, run_id: UUID, registration_id: UUID) -> RunRegistration:
        registration = await self.reg_repo.get_by_id(registration_id)
        if registration is None or registration.run_id != run_id:
            raise NotFoundError("Registration not found.")
        return registration

    async def check_in(
        self, run_id: UUID, registration_id: UUID, actor: CurrentUser
    ) -> RunRegistration:
        run = await self._managed_run(run_id, actor)
        registration = await self._load_registration(run_id, registration_id)
        if registration.status != RegistrationStatus.confirmed:
            raise ConflictError("Only confirmed players can be checked in.", code="not_confirmed")
        registration.status = RegistrationStatus.checked_in
        registration.checked_in_at = datetime.now(UTC)
        await self.audit.record(
            actor_id=actor.id,
            event_type="registration.checked_in",
            entity_type="RunRegistration",
            entity_id=registration.id,
            metadata={"run_id": str(run.id)},
        )
        await self.db.commit()
        await self.db.refresh(registration)
        checkins_total.inc()
        return registration

    async def mark_no_show(
        self, run_id: UUID, registration_id: UUID, actor: CurrentUser
    ) -> RunRegistration:
        run = await self._managed_run(run_id, actor)
        registration = await self._load_registration(run_id, registration_id)
        if registration.status not in (
            RegistrationStatus.confirmed,
            RegistrationStatus.checked_in,
        ):
            raise ConflictError(
                "Only confirmed/checked-in players can be marked no-show.",
                code="not_attendable",
            )
        registration.status = RegistrationStatus.no_show
        await self.audit.record(
            actor_id=actor.id,
            event_type="registration.no_show",
            entity_type="RunRegistration",
            entity_id=registration.id,
            metadata={"run_id": str(run.id)},
        )
        await self.db.commit()
        await self.db.refresh(registration)
        return registration
