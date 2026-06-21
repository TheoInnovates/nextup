"""Exhaustive unit tests for the pure scheduling engine."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from app.scheduling.engine import (
    RunSchedulingParams,
    compute_assignment,
    players_per_game,
)

START = datetime(2026, 7, 1, 18, 0, tzinfo=UTC)


def _params(**overrides: object) -> RunSchedulingParams:
    base = {
        "start_time": START,
        "end_time": START + timedelta(hours=3),
        "players_per_team": 5,
        "number_of_courts": 1,
        "estimated_game_minutes": 12,
        "arrival_lead_minutes": 15,
    }
    base.update(overrides)
    return RunSchedulingParams(**base)  # type: ignore[arg-type]


def test_players_per_game() -> None:
    assert players_per_game(_params(players_per_team=5, number_of_courts=1)) == 10
    assert players_per_game(_params(players_per_team=5, number_of_courts=2)) == 20
    assert players_per_game(_params(players_per_team=3, number_of_courts=3)) == 18


def test_first_position_plays_at_start() -> None:
    a = compute_assignment(_params(), 0)
    assert a.slot_number == 0
    assert a.estimated_play_time == START
    assert a.assigned_arrival_time == START - timedelta(minutes=15)


def test_arrival_may_precede_start_but_play_never_does() -> None:
    a = compute_assignment(_params(arrival_lead_minutes=30), 0)
    assert a.assigned_arrival_time < START
    assert a.estimated_play_time >= START


def test_positions_in_first_game_share_slot_zero() -> None:
    params = _params(players_per_team=5, number_of_courts=1)  # ppg = 10
    for position in range(10):
        assert compute_assignment(params, position).slot_number == 0


def test_next_game_increments_slot_and_time() -> None:
    params = _params(players_per_team=5, number_of_courts=1, estimated_game_minutes=12)
    a = compute_assignment(params, 10)  # first of the second game
    assert a.slot_number == 1
    assert a.estimated_play_time == START + timedelta(minutes=12)


def test_multiple_courts_increase_capacity_per_slot() -> None:
    params = _params(players_per_team=5, number_of_courts=2)  # ppg = 20
    assert compute_assignment(params, 19).slot_number == 0
    assert compute_assignment(params, 20).slot_number == 1


def test_deterministic() -> None:
    params = _params()
    assert compute_assignment(params, 7) == compute_assignment(params, 7)


def test_exceeds_run_window_flagged() -> None:
    # 60-min run, 12-min games, ppg=10 → slot 5 starts at +60m (== end), can't fit.
    params = _params(
        end_time=START + timedelta(minutes=60),
        players_per_team=5,
        number_of_courts=1,
        estimated_game_minutes=12,
    )
    within = compute_assignment(params, 0)
    assert within.exceeds_run_window is False
    overflow = compute_assignment(params, 50)  # slot 5 → play at +60m
    assert overflow.slot_number == 5
    assert overflow.exceeds_run_window is True


def test_last_fitting_game_not_flagged() -> None:
    # slot 4 starts at +48m, ends at +60m == end_time → fits exactly.
    params = _params(
        end_time=START + timedelta(minutes=60),
        players_per_team=5,
        number_of_courts=1,
        estimated_game_minutes=12,
    )
    a = compute_assignment(params, 40)  # slot 4
    assert a.slot_number == 4
    assert a.exceeds_run_window is False


def test_negative_position_rejected() -> None:
    with pytest.raises(ValueError, match="confirmed_position"):
        compute_assignment(_params(), -1)
