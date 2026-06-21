"""Cancellation + waitlist promotion + notification tests (functional)."""

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


async def test_cancel_confirmed_promotes_waitlister(
    client: AsyncClient, auth_headers: Headers
) -> None:
    org = _organizer(auth_headers)
    run = await _published_run(client, org)  # capacity 2
    rid = run["id"]
    pa, pb, pc = (_player(auth_headers, s) for s in ("pa", "pb", "pc"))
    assert (await _register(client, rid, pa))["status"] == "confirmed"
    assert (await _register(client, rid, pb))["status"] == "confirmed"
    assert (await _register(client, rid, pc))["status"] == "waitlisted"

    # pa cancels -> pc is promoted.
    assert (
        await client.delete(f"/api/v1/runs/{rid}/registrations/me", headers=pa)
    ).status_code == 204

    pc_reg = (await client.get(f"/api/v1/runs/{rid}/registrations/me", headers=pc)).json()
    assert pc_reg["status"] == "confirmed"
    assert pc_reg["assigned_slot_number"] is not None
    assert pc_reg["queue_position"] is None

    # pc was notified.
    notes = (await client.get("/api/v1/notifications", headers=pc)).json()
    assert any(n["type"] == "waitlist_promoted" for n in notes["items"])


async def test_cancel_waitlisted_recomputes_queue(
    client: AsyncClient, auth_headers: Headers
) -> None:
    org = _organizer(auth_headers)
    run = await _published_run(client, org)
    rid = run["id"]
    pa, pb, pc, pd = (_player(auth_headers, s) for s in ("pa", "pb", "pc", "pd"))
    await _register(client, rid, pa)
    await _register(client, rid, pb)
    assert (await _register(client, rid, pc))["queue_position"] == 1
    assert (await _register(client, rid, pd))["queue_position"] == 2

    # pc (queue #1) cancels -> pd moves up to #1, still no promotion.
    assert (
        await client.delete(f"/api/v1/runs/{rid}/registrations/me", headers=pc)
    ).status_code == 204
    pd_reg = (await client.get(f"/api/v1/runs/{rid}/registrations/me", headers=pd)).json()
    assert pd_reg["status"] == "waitlisted"
    assert pd_reg["queue_position"] == 1


async def test_cancel_not_registered_404(client: AsyncClient, auth_headers: Headers) -> None:
    org = _organizer(auth_headers)
    run = await _published_run(client, org)
    resp = await client.delete(
        f"/api/v1/runs/{run['id']}/registrations/me", headers=_player(auth_headers, "ghost")
    )
    assert resp.status_code == 404


async def test_reregister_after_cancel(client: AsyncClient, auth_headers: Headers) -> None:
    org = _organizer(auth_headers)
    run = await _published_run(client, org)
    rid = run["id"]
    player = _player(auth_headers, "pa")
    await _register(client, rid, player)
    await client.delete(f"/api/v1/runs/{rid}/registrations/me", headers=player)
    again = await client.post(f"/api/v1/runs/{rid}/registrations", headers=player)
    assert again.status_code == 201
    assert again.json()["status"] == "confirmed"


async def test_organizer_cancels_a_registration(client: AsyncClient, auth_headers: Headers) -> None:
    org = _organizer(auth_headers)
    run = await _published_run(client, org)
    rid = run["id"]
    player = _player(auth_headers, "pa")
    reg = await _register(client, rid, player)
    resp = await client.delete(f"/api/v1/runs/{rid}/registrations/{reg['id']}", headers=org)
    assert resp.status_code == 204
    # The player is no longer actively registered.
    assert (
        await client.get(f"/api/v1/runs/{rid}/registrations/me", headers=player)
    ).status_code == 404


async def test_manual_promote_after_capacity_increase(
    client: AsyncClient, auth_headers: Headers
) -> None:
    org = _organizer(auth_headers)
    run = await _published_run(client, org)  # capacity 2
    rid = run["id"]
    pa, pb, pc = (_player(auth_headers, s) for s in ("pa", "pb", "pc"))
    await _register(client, rid, pa)
    await _register(client, rid, pb)
    pc_reg = await _register(client, rid, pc)  # waitlisted
    # Increase capacity, then manually promote the waitlisted player.
    await client.patch(f"/api/v1/runs/{rid}", headers=org, json={"maximum_players": 3})
    resp = await client.post(
        f"/api/v1/runs/{rid}/registrations/{pc_reg['id']}/promote", headers=org
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "confirmed"


async def test_manual_promote_when_full_conflict(
    client: AsyncClient, auth_headers: Headers
) -> None:
    org = _organizer(auth_headers)
    run = await _published_run(client, org)  # capacity 2
    rid = run["id"]
    pa, pb, pc = (_player(auth_headers, s) for s in ("pa", "pb", "pc"))
    await _register(client, rid, pa)
    await _register(client, rid, pb)
    pc_reg = await _register(client, rid, pc)  # waitlisted, run full
    resp = await client.post(
        f"/api/v1/runs/{rid}/registrations/{pc_reg['id']}/promote", headers=org
    )
    assert resp.status_code == 409
    assert resp.json()["code"] == "run_full"


async def test_mark_notification_read(client: AsyncClient, auth_headers: Headers) -> None:
    org = _organizer(auth_headers)
    run = await _published_run(client, org)
    rid = run["id"]
    pa, pb, pc = (_player(auth_headers, s) for s in ("pa", "pb", "pc"))
    await _register(client, rid, pa)
    await _register(client, rid, pb)
    await _register(client, rid, pc)
    await client.delete(f"/api/v1/runs/{rid}/registrations/me", headers=pa)  # promotes pc
    notes = (await client.get("/api/v1/notifications", headers=pc)).json()["items"]
    assert notes
    note_id = notes[0]["id"]
    read = await client.post(f"/api/v1/notifications/{note_id}/read", headers=pc)
    assert read.status_code == 200
    assert read.json()["is_read"] is True
