"""Run endpoint tests: creation, lifecycle transitions, visibility, validation."""

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


def _run_payload(gym_id: str, **overrides: object) -> dict:
    start = datetime.now(UTC) + timedelta(days=7)
    payload = {
        "gym_id": gym_id,
        "title": "Tuesday Run",
        "description": "Weekly pickup",
        "start_time": start.isoformat(),
        "end_time": (start + timedelta(hours=2)).isoformat(),
        "registration_opens_at": (start - timedelta(days=5)).isoformat(),
        "registration_closes_at": (start - timedelta(hours=1)).isoformat(),
        "cancellation_deadline": (start - timedelta(hours=2)).isoformat(),
        "maximum_players": 20,
        "players_per_team": 5,
        "number_of_courts": 2,
        "estimated_game_minutes": 12,
        "arrival_lead_minutes": 15,
    }
    payload.update(overrides)
    return payload


async def _make_gym(client: AsyncClient, headers: dict[str, str]) -> str:
    resp = await client.post("/api/v1/gyms", headers=headers, json=_GYM)
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _make_run(
    client: AsyncClient, headers: dict[str, str], gym_id: str, **overrides: object
) -> dict:
    resp = await client.post(
        "/api/v1/runs", headers=headers, json=_run_payload(gym_id, **overrides)
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


# --- creation + authz --------------------------------------------------------
async def test_create_run_as_organizer(client: AsyncClient, auth_headers: Headers) -> None:
    headers = _organizer(auth_headers)
    gym_id = await _make_gym(client, headers)
    run = await _make_run(client, headers, gym_id)
    assert run["status"] == "draft"
    assert run["gym_id"] == gym_id
    assert run["organizer_user_id"]


async def test_create_run_other_gym_forbidden(client: AsyncClient, auth_headers: Headers) -> None:
    gym_id = await _make_gym(client, _organizer(auth_headers, "org-A"))
    resp = await client.post(
        "/api/v1/runs",
        headers=_organizer(auth_headers, "org-B"),
        json=_run_payload(gym_id),
    )
    assert resp.status_code == 403


async def test_create_run_as_player_forbidden(client: AsyncClient, auth_headers: Headers) -> None:
    gym_id = await _make_gym(client, _organizer(auth_headers))
    resp = await client.post(
        "/api/v1/runs",
        headers=auth_headers(roles=("player",), sub="p1"),
        json=_run_payload(gym_id),
    )
    assert resp.status_code == 403


async def test_invalid_time_window_rejected(client: AsyncClient, auth_headers: Headers) -> None:
    headers = _organizer(auth_headers)
    gym_id = await _make_gym(client, headers)
    start = datetime.now(UTC) + timedelta(days=7)
    bad = _run_payload(
        gym_id,
        end_time=(start - timedelta(hours=1)).isoformat(),  # end before start
    )
    resp = await client.post("/api/v1/runs", headers=headers, json=bad)
    assert resp.status_code == 422


# --- visibility --------------------------------------------------------------
async def test_draft_hidden_from_players(client: AsyncClient, auth_headers: Headers) -> None:
    org = _organizer(auth_headers)
    gym_id = await _make_gym(client, org)
    run = await _make_run(client, org, gym_id)
    player = auth_headers(roles=("player",), sub="p2")

    # Draft: invisible to a player.
    assert (await client.get(f"/api/v1/runs/{run['id']}", headers=player)).status_code == 404
    listed = (await client.get("/api/v1/runs", headers=player)).json()["items"]
    assert run["id"] not in {r["id"] for r in listed}

    # After publish: visible.
    pub = await client.post(f"/api/v1/runs/{run['id']}/publish", headers=org)
    assert pub.status_code == 200
    assert (await client.get(f"/api/v1/runs/{run['id']}", headers=player)).status_code == 200
    listed_after = (await client.get("/api/v1/runs", headers=player)).json()["items"]
    assert run["id"] in {r["id"] for r in listed_after}


# --- lifecycle ---------------------------------------------------------------
async def test_full_lifecycle(client: AsyncClient, auth_headers: Headers) -> None:
    org = _organizer(auth_headers)
    gym_id = await _make_gym(client, org)
    run = await _make_run(client, org, gym_id)
    rid = run["id"]
    assert (await client.post(f"/api/v1/runs/{rid}/publish", headers=org)).json()[
        "status"
    ] == "published"
    assert (await client.post(f"/api/v1/runs/{rid}/start", headers=org)).json()[
        "status"
    ] == "in_progress"
    assert (await client.post(f"/api/v1/runs/{rid}/complete", headers=org)).json()[
        "status"
    ] == "completed"


async def test_invalid_transition_returns_409(client: AsyncClient, auth_headers: Headers) -> None:
    org = _organizer(auth_headers)
    gym_id = await _make_gym(client, org)
    run = await _make_run(client, org, gym_id)
    # draft -> completed is not allowed.
    resp = await client.post(f"/api/v1/runs/{run['id']}/complete", headers=org)
    assert resp.status_code == 409
    assert resp.json()["code"] == "invalid_transition"


async def test_cancel_then_no_further_transitions(
    client: AsyncClient, auth_headers: Headers
) -> None:
    org = _organizer(auth_headers)
    gym_id = await _make_gym(client, org)
    run = await _make_run(client, org, gym_id)
    assert (await client.delete(f"/api/v1/runs/{run['id']}", headers=org)).status_code == 204
    # Cancelled is terminal.
    resp = await client.post(f"/api/v1/runs/{run['id']}/publish", headers=org)
    assert resp.status_code == 409


async def test_other_organizer_cannot_manage(client: AsyncClient, auth_headers: Headers) -> None:
    gym_id = await _make_gym(client, _organizer(auth_headers, "org-A"))
    run = await _make_run(client, _organizer(auth_headers, "org-A"), gym_id)
    resp = await client.post(
        f"/api/v1/runs/{run['id']}/publish", headers=_organizer(auth_headers, "org-B")
    )
    assert resp.status_code == 403


async def test_admin_can_manage_others_run(client: AsyncClient, auth_headers: Headers) -> None:
    gym_id = await _make_gym(client, _organizer(auth_headers, "org-A"))
    run = await _make_run(client, _organizer(auth_headers, "org-A"), gym_id)
    resp = await client.post(
        f"/api/v1/runs/{run['id']}/publish",
        headers=auth_headers(roles=("admin",), sub="adm"),
    )
    assert resp.status_code == 200


# --- updates -----------------------------------------------------------------
async def test_update_run_title(client: AsyncClient, auth_headers: Headers) -> None:
    org = _organizer(auth_headers)
    gym_id = await _make_gym(client, org)
    run = await _make_run(client, org, gym_id)
    resp = await client.patch(
        f"/api/v1/runs/{run['id']}", headers=org, json={"title": "Renamed Run"}
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Renamed Run"


async def test_update_rejected_after_completed(client: AsyncClient, auth_headers: Headers) -> None:
    org = _organizer(auth_headers)
    gym_id = await _make_gym(client, org)
    run = await _make_run(client, org, gym_id)
    rid = run["id"]
    await client.post(f"/api/v1/runs/{rid}/publish", headers=org)
    await client.post(f"/api/v1/runs/{rid}/start", headers=org)
    await client.post(f"/api/v1/runs/{rid}/complete", headers=org)
    resp = await client.patch(f"/api/v1/runs/{rid}", headers=org, json={"title": "Too late"})
    assert resp.status_code == 409
    assert resp.json()["code"] == "not_editable"
