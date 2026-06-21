"""Registration business logic — the concurrency-critical path.

A registration runs in a single transaction that **locks the run row**
(``SELECT … FOR UPDATE``) before counting confirmed registrations, so two players
cannot both claim the final slot (spec §9/§15). The post-lock counts observe
each other's committed inserts because the run-row lock serialises all
registration attempts for a run — correct under PostgreSQL's default
READ COMMITTED isolation (do not raise isolation without revisiting this).
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.core.logging import get_logger
from app.core.metrics import registrations_total
from app.enums import RegistrationStatus, RunStatus
from app.models.registration import RunRegistration
from app.models.run import BasketballRun
from app.repositories.registration import RegistrationRepository
from app.scheduling.engine import RunSchedulingParams, compute_assignment

log = get_logger(__name__)


def build_scheduling_params(run: BasketballRun) -> RunSchedulingParams:
    """Map a run's capacity/timing fields to the pure engine's params."""
    return RunSchedulingParams(
        start_time=run.start_time,
        end_time=run.end_time,
        players_per_team=run.players_per_team,
        number_of_courts=run.number_of_courts,
        estimated_game_minutes=run.estimated_game_minutes,
        arrival_lead_minutes=run.arrival_lead_minutes,
    )


class RegistrationService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = RegistrationRepository(db)

    async def register(self, run_id: UUID, player_id: UUID) -> RunRegistration:
        # FOR UPDATE on the run row: the serialization point for the final-slot
        # race. First statement on a fresh request session, so it is not served
        # from the identity map (verified by the concurrency test).
        run = await self.db.get(BasketballRun, run_id, with_for_update=True)
        if run is None:
            raise NotFoundError("Run not found.")
        self._assert_open_for_registration(run)

        if await self.repo.get_active_for_player(run_id, player_id) is not None:
            raise ConflictError(
                "You are already registered for this run.", code="already_registered"
            )

        occupying = await self.repo.count_occupying(run_id)
        registration = RunRegistration(
            run_id=run_id,
            player_user_id=player_id,
            registered_at=datetime.now(UTC),
        )
        if occupying < run.maximum_players:
            self._assign_confirmed(registration, run, confirmed_position=occupying)
        else:
            waitlisted = await self.repo.count_waitlisted(run_id)
            registration.status = RegistrationStatus.waitlisted
            registration.queue_position = waitlisted + 1

        try:
            await self.repo.add(registration)
            await self.db.commit()
        except IntegrityError as exc:
            # Backstop: the partial unique index also guards duplicates if the
            # lock were ever bypassed. Translate to a 409 rather than a 500.
            await self.db.rollback()
            raise ConflictError(
                "You are already registered for this run.", code="already_registered"
            ) from exc

        await self.db.refresh(registration)
        registrations_total.labels(result=registration.status.value).inc()
        return registration

    async def get_for_player(self, run_id: UUID, player_id: UUID) -> RunRegistration:
        registration = await self.repo.get_active_for_player(run_id, player_id)
        if registration is None:
            raise NotFoundError("You are not registered for this run.")
        return registration

    def _assign_confirmed(
        self, registration: RunRegistration, run: BasketballRun, *, confirmed_position: int
    ) -> None:
        assignment = compute_assignment(build_scheduling_params(run), confirmed_position)
        if assignment.exceeds_run_window:
            # maximum_players allows more confirmed players than fit in the run
            # window — a capacity misconfiguration. Confirm the slot but surface it.
            log.warning(
                "registration.slot_exceeds_run_window",
                run_id=str(run.id),
                confirmed_position=confirmed_position,
                slot_number=assignment.slot_number,
            )
        registration.status = RegistrationStatus.confirmed
        registration.assigned_slot_number = assignment.slot_number
        registration.estimated_play_time = assignment.estimated_play_time
        registration.assigned_arrival_time = assignment.assigned_arrival_time
        registration.queue_position = None

    def _assert_open_for_registration(self, run: BasketballRun) -> None:
        if run.status != RunStatus.published:
            raise ConflictError(
                "Registration is not open for this run.",
                code="registration_not_open",
            )
        now = datetime.now(UTC)
        if now < run.registration_opens_at:
            raise ConflictError("Registration has not opened yet.", code="registration_not_open")
        if now > run.registration_closes_at:
            raise ConflictError("Registration has closed.", code="registration_closed")
