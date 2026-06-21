"""Cancellation + waitlist promotion (atomic, run-row locked).

Cancelling a confirmed player frees a slot; the earliest eligible waitlisted
player is promoted, and confirmed slot/times + waitlist queue positions are
recomputed deterministically — all in one transaction under the run-row
``SELECT … FOR UPDATE`` lock (the same serialization point as registration), so
concurrent cancel/register/promote operations can't violate capacity.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.authz import assert_can_manage
from app.core.dependencies import CurrentUser
from app.core.exceptions import ConflictError, NotFoundError
from app.core.metrics import promotions_total
from app.enums import NotificationType, RegistrationStatus
from app.models.registration import RunRegistration
from app.models.run import BasketballRun
from app.repositories.registration import ACTIVE_STATUSES, RegistrationRepository
from app.scheduling.engine import compute_assignment
from app.services.audit import AuditService
from app.services.notification import NotificationService
from app.services.registration import build_scheduling_params


@dataclass
class CancellationResult:
    cancelled: RunRegistration
    promoted: list[RunRegistration] = field(default_factory=list)


class CancellationService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = RegistrationRepository(db)
        self.notifications = NotificationService(db)
        self.audit = AuditService(db)

    async def cancel_own(self, run_id: UUID, actor: CurrentUser) -> CancellationResult:
        run = await self._lock_run(run_id)
        registration = await self.repo.get_active_for_player(run_id, actor.id)
        if registration is None:
            raise NotFoundError("You are not registered for this run.")
        return await self._cancel_and_promote(run, registration, actor)

    async def cancel_registration(
        self, run_id: UUID, registration_id: UUID, actor: CurrentUser
    ) -> CancellationResult:
        run = await self._lock_run(run_id)
        assert_can_manage(run.organizer_user_id, actor, "You do not manage this run.")
        registration = await self._load_registration(run_id, registration_id)
        if registration.status not in ACTIVE_STATUSES:
            raise ConflictError("Registration is not active.", code="not_active")
        return await self._cancel_and_promote(run, registration, actor)

    async def promote_manual(
        self, run_id: UUID, registration_id: UUID, actor: CurrentUser
    ) -> RunRegistration:
        run = await self._lock_run(run_id)
        assert_can_manage(run.organizer_user_id, actor, "You do not manage this run.")
        registration = await self._load_registration(run_id, registration_id)
        if registration.status != RegistrationStatus.waitlisted:
            raise ConflictError(
                "Only waitlisted registrations can be promoted.", code="not_waitlisted"
            )
        occupying = await self.repo.count_occupying(run_id)
        if occupying >= run.maximum_players:
            raise ConflictError("The run is full.", code="run_full")
        registration.status = RegistrationStatus.confirmed
        await self.db.flush()
        await self._recompute(run)
        await self.notifications.create(
            user_id=registration.player_user_id,
            type=NotificationType.waitlist_promoted,
            title="You're confirmed!",
            message=f"You've been promoted to a confirmed spot for {run.title}.",
            related_run_id=run.id,
        )
        await self.audit.record(
            actor_id=actor.id,
            event_type="registration.promoted",
            entity_type="RunRegistration",
            entity_id=registration.id,
            metadata={"run_id": str(run.id), "manual": True},
        )
        await self.db.commit()
        await self.db.refresh(registration)
        promotions_total.inc()
        return registration

    # --- internals -----------------------------------------------------------
    async def _lock_run(self, run_id: UUID) -> BasketballRun:
        run = await self.db.get(BasketballRun, run_id, with_for_update=True)
        if run is None:
            raise NotFoundError("Run not found.")
        return run

    async def _load_registration(self, run_id: UUID, registration_id: UUID) -> RunRegistration:
        registration = await self.repo.get_by_id(registration_id)
        if registration is None or registration.run_id != run_id:
            raise NotFoundError("Registration not found.")
        return registration

    async def _cancel_and_promote(
        self, run: BasketballRun, registration: RunRegistration, actor: CurrentUser
    ) -> CancellationResult:
        registration.status = RegistrationStatus.cancelled
        registration.cancelled_at = datetime.now(UTC)
        registration.queue_position = None
        registration.assigned_slot_number = None
        registration.estimated_play_time = None
        registration.assigned_arrival_time = None
        await self.db.flush()

        promoted = await self._recompute(run)

        await self.audit.record(
            actor_id=actor.id,
            event_type="registration.cancelled",
            entity_type="RunRegistration",
            entity_id=registration.id,
            metadata={
                "run_id": str(run.id),
                "player_user_id": str(registration.player_user_id),
            },
        )
        for promotion in promoted:
            await self.notifications.create(
                user_id=promotion.player_user_id,
                type=NotificationType.waitlist_promoted,
                title="You're in!",
                message=f"A spot opened up — you're confirmed for {run.title}.",
                related_run_id=run.id,
            )
            await self.audit.record(
                actor_id=actor.id,
                event_type="registration.promoted",
                entity_type="RunRegistration",
                entity_id=promotion.id,
                metadata={"run_id": str(run.id)},
            )

        await self.db.commit()
        await self.db.refresh(registration)
        if promoted:
            promotions_total.inc(len(promoted))
        return CancellationResult(cancelled=registration, promoted=promoted)

    async def _recompute(self, run: BasketballRun) -> list[RunRegistration]:
        """Promote earliest waitlisters into free slots, then recompute all
        confirmed slot/times and waitlist queue positions. Returns promotions."""
        occupying = await self.repo.list_occupying_ordered(run.id)
        waitlist = await self.repo.list_waitlisted_ordered(run.id)

        promoted: list[RunRegistration] = []
        index = 0
        while len(occupying) < run.maximum_players and index < len(waitlist):
            promotion = waitlist[index]
            index += 1
            promotion.status = RegistrationStatus.confirmed
            occupying.append(promotion)
            promoted.append(promotion)
        remaining_waitlist = waitlist[index:]

        # Deterministic order for slot assignment.
        occupying.sort(key=lambda r: (r.registered_at, str(r.id)))
        params = build_scheduling_params(run)
        for position, reg in enumerate(occupying):
            assignment = compute_assignment(params, position)
            reg.assigned_slot_number = assignment.slot_number
            reg.estimated_play_time = assignment.estimated_play_time
            reg.assigned_arrival_time = assignment.assigned_arrival_time
            reg.queue_position = None

        for offset, reg in enumerate(remaining_waitlist):
            reg.queue_position = offset + 1
            reg.assigned_slot_number = None
            reg.estimated_play_time = None
            reg.assigned_arrival_time = None

        await self.db.flush()
        return promoted
