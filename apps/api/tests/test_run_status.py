"""Pure status-machine tests (no DB/HTTP)."""

from __future__ import annotations

import pytest
from app.core.exceptions import ConflictError
from app.enums import RunStatus
from app.services.run import assert_transition, can_transition


def test_valid_transitions() -> None:
    assert can_transition(RunStatus.draft, RunStatus.published)
    assert can_transition(RunStatus.published, RunStatus.registration_closed)
    assert can_transition(RunStatus.published, RunStatus.in_progress)
    assert can_transition(RunStatus.registration_closed, RunStatus.in_progress)
    assert can_transition(RunStatus.in_progress, RunStatus.completed)


def test_cancel_reachable_from_any_non_terminal() -> None:
    for state in (
        RunStatus.draft,
        RunStatus.published,
        RunStatus.registration_closed,
        RunStatus.in_progress,
    ):
        assert can_transition(state, RunStatus.cancelled)


def test_invalid_transitions() -> None:
    assert not can_transition(RunStatus.draft, RunStatus.completed)
    assert not can_transition(RunStatus.draft, RunStatus.in_progress)
    assert not can_transition(RunStatus.completed, RunStatus.published)
    assert not can_transition(RunStatus.cancelled, RunStatus.published)
    assert not can_transition(RunStatus.completed, RunStatus.cancelled)


def test_assert_transition_raises_conflict() -> None:
    with pytest.raises(ConflictError):
        assert_transition(RunStatus.completed, RunStatus.published)
