"""Roster + check-in/no-show tests (attendance authz + status changes)."""

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
        "start_time": start.isoformat(),
        "end_time": (start + timedelta(hours=2)).isoformat(),
        "registration_opens_at": (now - timedelta(days=1)).isoformat(),
        "registration_closes_at": (now + timedelta(hours=1)).isoformat(),
        "cancellation_deadline": (now + timedelta(minutes=30)).isoformat(),
        "maximum_players": 2,
        "players_per_team": 5,
        "number_of_courts": 1,
        "estimated_game_minutes": 12,
        "arrival_lead_minutes": 15,
    }
    payload.update(overrides)
    return payload


async def _published_run(client: AsyncClient, org: dict[str, str], **overrides: object) -> dict:
    gym_id = (await client.post("/api/v1/gyms", headers=org, json=_GYM)).json()["id"]
    run = (
        await client.post("/api/v1/runs", headers=org, json=_open_run_payload(gym_id, **overrides))
    ).json()
    await client.post(f"/api/v1/runs/{run['id']}/publish", headers=org)
    return run


async def _register(client: AsyncClient, run_id: str, player: dict[str, str]) -> dict:
    resp = await client.post(f"/api/v1/runs/{run_id}/registrations", headers=player)
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_roster_shows_confirmed_and_waitlist(
    client: AsyncClient, auth_headers: Headers
) -> None:
    org = _organizer(auth_headers)
    run = await _published_run(client, org)
    rid = run["id"]
    await _register(client, rid, _player(auth_headers, "pa"))
    await _register(client, rid, _player(auth_headers, "pb"))
    await _register(client, rid, _player(auth_headers, "pc"))  # waitlisted

    roster = (await client.get(f"/api/v1/runs/{rid}/roster", headers=org)).json()
    assert len(roster["confirmed"]) == 2
    assert len(roster["waitlist"]) == 1
    assert roster["waitlist"][0]["player_email"] == "pc@ex.com"
    assert all(e["player_display_name"] for e in roster["confirmed"])


async def test_roster_forbidden_for_non_owner(client: AsyncClient, auth_headers: Headers) -> None:
    run = await _published_run(client, _organizer(auth_headers, "org-A"))
    resp = await client.get(
        f"/api/v1/runs/{run['id']}/roster", headers=_organizer(auth_headers, "org-B")
    )
    assert resp.status_code == 403


async def test_check_in(client: AsyncClient, auth_headers: Headers) -> None:
    org = _organizer(auth_headers)
    run = await _published_run(client, org)
    rid = run["id"]
    reg = await _register(client, rid, _player(auth_headers, "pa"))
    resp = await client.post(f"/api/v1/runs/{rid}/registrations/{reg['id']}/check-in", headers=org)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "checked_in"
    assert body["checked_in_at"] is not None


async def test_check_in_forbidden_for_non_owner(client: AsyncClient, auth_headers: Headers) -> None:
    org = _organizer(auth_headers, "org-A")
    run = await _published_run(client, org)
    rid = run["id"]
    reg = await _register(client, rid, _player(auth_headers, "pa"))
    resp = await client.post(
        f"/api/v1/runs/{rid}/registrations/{reg['id']}/check-in",
        headers=_organizer(auth_headers, "org-B"),
    )
    assert resp.status_code == 403


async def test_check_in_waitlisted_conflict(client: AsyncClient, auth_headers: Headers) -> None:
    org = _organizer(auth_headers)
    run = await _published_run(client, org)
    rid = run["id"]
    await _register(client, rid, _player(auth_headers, "pa"))
    await _register(client, rid, _player(auth_headers, "pb"))
    waitlisted = await _register(client, rid, _player(auth_headers, "pc"))
    resp = await client.post(
        f"/api/v1/runs/{rid}/registrations/{waitlisted['id']}/check-in", headers=org
    )
    assert resp.status_code == 409
    assert resp.json()["code"] == "not_confirmed"


async def test_no_show(client: AsyncClient, auth_headers: Headers) -> None:
    org = _organizer(auth_headers)
    run = await _published_run(client, org)
    rid = run["id"]
    reg = await _register(client, rid, _player(auth_headers, "pa"))
    resp = await client.post(f"/api/v1/runs/{rid}/registrations/{reg['id']}/no-show", headers=org)
    assert resp.status_code == 200
    assert resp.json()["status"] == "no_show"
    roster = (await client.get(f"/api/v1/runs/{rid}/roster", headers=org)).json()
    assert len(roster["no_show"]) == 1
