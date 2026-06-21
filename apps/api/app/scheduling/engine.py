"""Deterministic scheduling engine (pure — no DB, no HTTP).

Implements the formula in docs/DATA_MODEL.md:

    players_per_game   = players_per_team * 2 * number_of_courts
    slot_number        = floor(confirmed_position / players_per_game)   # 0-based
    estimated_play_time   = start_time + slot_number * estimated_game_minutes
    assigned_arrival_time = estimated_play_time - arrival_lead_minutes

Invariants (unit-tested):
* Deterministic for a given input.
* Arrival time may precede ``start_time`` (it's when to show up); the **play
  time** never precedes ``start_time``.
* A game that cannot complete before ``end_time`` is *flagged*
  (``exceeds_run_window``) rather than silently scheduled — a capacity signal.
* Accounts for multiple courts and capacity via ``players_per_game``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True)
class RunSchedulingParams:
    start_time: datetime
    end_time: datetime
    players_per_team: int
    number_of_courts: int
    estimated_game_minutes: int
    arrival_lead_minutes: int


@dataclass(frozen=True)
class SlotAssignment:
    confirmed_position: int  # 0-based index among active confirmed registrations
    slot_number: int
    estimated_play_time: datetime
    assigned_arrival_time: datetime
    exceeds_run_window: bool


def players_per_game(params: RunSchedulingParams) -> int:
    """Number of confirmed players that can be on court simultaneously."""
    return params.players_per_team * 2 * params.number_of_courts


def compute_assignment(params: RunSchedulingParams, confirmed_position: int) -> SlotAssignment:
    """Compute the slot/arrival/play time for a 0-based confirmed position."""
    if confirmed_position < 0:
        raise ValueError("confirmed_position must be >= 0")
    capacity_per_game = players_per_game(params)
    if capacity_per_game <= 0:
        raise ValueError("players_per_game must be positive")

    slot_number = confirmed_position // capacity_per_game
    play_offset = timedelta(minutes=slot_number * params.estimated_game_minutes)
    estimated_play_time = params.start_time + play_offset
    assigned_arrival_time = estimated_play_time - timedelta(minutes=params.arrival_lead_minutes)
    game_end = estimated_play_time + timedelta(minutes=params.estimated_game_minutes)
    exceeds_run_window = game_end > params.end_time

    return SlotAssignment(
        confirmed_position=confirmed_position,
        slot_number=slot_number,
        estimated_play_time=estimated_play_time,
        assigned_arrival_time=assigned_arrival_time,
        exceeds_run_window=exceeds_run_window,
    )
