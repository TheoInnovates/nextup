"""Registration endpoint tests: confirm/waitlist assignment, duplicates, window."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from httpx import AsyncClient

Headers = Callable[..., dict[str, str]]

_GYM = {
    "name": "Rec Center",
    "address_line_1": "1 Main",
    "city": "Boston",
    "state": "MA",
    "postal_code": "02108",
    "timezone": "America/New_York",
}


def _organizer(auth_headers: Headers, sub: str = "org-A") -> dict[str, str]:
    return auth_headers(roles=("organizer",), sub=sub, email=f"{sub}@ex.com")


def _player(auth_headers: Headers, sub: str) -> dict[str, str]:
    return auth_headers(roles=("player",), sub=sub, email=f"{sub}@ex.com")


def _open_run_payload(gym_id: str, **overrides: object) -> dict:
    now = datetime.now(UTC)
    start = now + timedelta(hours=3)
    payload = {
        "gym_id": gym_id,
        "title": "Open Run",
        "description": None,
        "start_time": start.isoformat(),
        "end_time": (start + timedelta(hours=2)).isoformat(),
        "registration_opens_at": (now - timedelta(days=1)).isoformat(),
        "registration_closes_at": (now + timedelta(hours=1)).isoformat(),
        "cancellation_deadline": (now + timedelta(minutes=30)).isoformat(),
        "maximum_players": 20,
        "players_per_team": 5,
        "number_of_courts": 2,
        "estimated_game_minutes": 12,
        "arrival_lead_minutes": 15,
    }
    payload.update(overrides)
    return payload


async def _published_run(
    client: AsyncClient, org: dict[str, str], *, publish: bool = True, **overrides: object
) -> dict:
    gym_id = (await client.post("/api/v1/gyms", headers=org, json=_GYM)).json()["id"]
    run = (
        await client.post("/api/v1/runs", headers=org, json=_open_run_payload(gym_id, **overrides))
    ).json()
    if publish:
        await client.post(f"/api/v1/runs/{run['id']}/publish", headers=org)
    return run


async def test_register_confirmed_with_timing(client: AsyncClient, auth_headers: Headers) -> None:
    org = _organizer(auth_headers)
    run = await _published_run(client, org)  # ppg = 5*2*2 = 20, capacity 20
    resp = await client.post(
        f"/api/v1/runs/{run['id']}/registrations", headers=_player(auth_headers, "p1")
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "confirmed"
    assert body["assigned_slot_number"] == 0
    assert body["queue_position"] is None
    # First confirmed player plays at start_time; arrives arrival_lead before.
    play = datetime.fromisoformat(body["estimated_play_time"])
    arrival = datetime.fromisoformat(body["assigned_arrival_time"])
    start = datetime.fromisoformat(run["start_time"])
    assert play == start
    assert arrival == start - timedelta(minutes=15)


async def test_register_waitlisted_when_full(client: AsyncClient, auth_headers: Headers) -> None:
    org = _organizer(auth_headers)
    # Minimum capacity is 2; fill it, then the third player waitlists.
    run = await _published_run(client, org, maximum_players=2)
    for sub in ("pa", "pb"):
        confirmed = await client.post(
            f"/api/v1/runs/{run['id']}/registrations", headers=_player(auth_headers, sub)
        )
        assert confirmed.json()["status"] == "confirmed"
    third = await client.post(
        f"/api/v1/runs/{run['id']}/registrations", headers=_player(auth_headers, "pc")
    )
    assert third.status_code == 201
    body = third.json()
    assert body["status"] == "waitlisted"
    assert body["queue_position"] == 1
    assert body["assigned_slot_number"] is None


async def test_duplicate_registration_conflict(client: AsyncClient, auth_headers: Headers) -> None:
    org = _organizer(auth_headers)
    run = await _published_run(client, org)
    player = _player(auth_headers, "dup")
    assert (
        await client.post(f"/api/v1/runs/{run['id']}/registrations", headers=player)
    ).status_code == 201
    again = await client.post(f"/api/v1/runs/{run['id']}/registrations", headers=player)
    assert again.status_code == 409
    assert again.json()["code"] == "already_registered"


async def test_register_requires_player_role(client: AsyncClient, auth_headers: Headers) -> None:
    org = _organizer(auth_headers)
    run = await _published_run(client, org)
    resp = await client.post(
        f"/api/v1/runs/{run['id']}/registrations",
        headers=auth_headers(roles=("admin",), sub="adm"),
    )
    assert resp.status_code == 403


async def test_register_draft_run_conflict(client: AsyncClient, auth_headers: Headers) -> None:
    org = _organizer(auth_headers)
    run = await _published_run(client, org, publish=False)  # stays draft
    resp = await client.post(
        f"/api/v1/runs/{run['id']}/registrations", headers=_player(auth_headers, "p2")
    )
    assert resp.status_code == 409
    assert resp.json()["code"] == "registration_not_open"


async def test_register_closed_window_conflict(client: AsyncClient, auth_headers: Headers) -> None:
    org = _organizer(auth_headers)
    now = datetime.now(UTC)
    start = now - timedelta(days=1)
    run = await _published_run(
        client,
        org,
        start_time=start.isoformat(),
        end_time=(start + timedelta(hours=2)).isoformat(),
        registration_opens_at=(now - timedelta(days=3)).isoformat(),
        registration_closes_at=(now - timedelta(days=2)).isoformat(),
        cancellation_deadline=(now - timedelta(days=2)).isoformat(),
    )
    resp = await client.post(
        f"/api/v1/runs/{run['id']}/registrations", headers=_player(auth_headers, "late")
    )
    assert resp.status_code == 409
    assert resp.json()["code"] == "registration_closed"


async def test_get_my_registration(client: AsyncClient, auth_headers: Headers) -> None:
    org = _organizer(auth_headers)
    run = await _published_run(client, org)
    player = _player(auth_headers, "me1")
    await client.post(f"/api/v1/runs/{run['id']}/registrations", headers=player)
    mine = await client.get(f"/api/v1/runs/{run['id']}/registrations/me", headers=player)
    assert mine.status_code == 200
    assert mine.json()["status"] == "confirmed"
    # A different player who didn't register gets 404.
    other = await client.get(
        f"/api/v1/runs/{run['id']}/registrations/me", headers=_player(auth_headers, "me2")
    )
    assert other.status_code == 404
