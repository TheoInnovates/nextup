"""Gym + Court CRUD, ownership/IDOR, visibility, and validation tests."""

from __future__ import annotations

from collections.abc import Callable

from httpx import AsyncClient

GYM_PAYLOAD = {
    "name": "Downtown Rec",
    "description": "Main gym",
    "address_line_1": "1 Main St",
    "city": "Boston",
    "state": "MA",
    "postal_code": "02108",
    "timezone": "America/New_York",
}

Headers = Callable[..., dict[str, str]]


def _organizer(auth_headers: Headers, sub: str = "org-A") -> dict[str, str]:
    return auth_headers(roles=("organizer",), sub=sub, email=f"{sub}@ex.com")


async def _create_gym(client: AsyncClient, headers: dict[str, str], **overrides: object) -> dict:
    resp = await client.post("/api/v1/gyms", headers=headers, json={**GYM_PAYLOAD, **overrides})
    assert resp.status_code == 201, resp.text
    return resp.json()


# --- gym CRUD + authz --------------------------------------------------------
async def test_create_gym_as_organizer(client: AsyncClient, auth_headers: Headers) -> None:
    body = await _create_gym(client, _organizer(auth_headers))
    assert body["name"] == "Downtown Rec"
    assert body["is_active"] is True
    assert body["owner_user_id"]


async def test_create_gym_forbidden_for_player(client: AsyncClient, auth_headers: Headers) -> None:
    resp = await client.post(
        "/api/v1/gyms",
        headers=auth_headers(roles=("player",), sub="p1"),
        json=GYM_PAYLOAD,
    )
    assert resp.status_code == 403
    assert resp.json()["code"] == "forbidden"


async def test_create_gym_invalid_timezone(client: AsyncClient, auth_headers: Headers) -> None:
    resp = await client.post(
        "/api/v1/gyms",
        headers=_organizer(auth_headers),
        json={**GYM_PAYLOAD, "timezone": "Mars/Phobos"},
    )
    assert resp.status_code == 422


async def test_get_gym(client: AsyncClient, auth_headers: Headers) -> None:
    gym = await _create_gym(client, _organizer(auth_headers))
    resp = await client.get(
        f"/api/v1/gyms/{gym['id']}", headers=auth_headers(roles=("player",), sub="p2")
    )
    assert resp.status_code == 200
    assert resp.json()["id"] == gym["id"]


async def test_get_missing_gym_404(client: AsyncClient, auth_headers: Headers) -> None:
    resp = await client.get(
        "/api/v1/gyms/00000000-0000-0000-0000-000000000000",
        headers=_organizer(auth_headers),
    )
    assert resp.status_code == 404


async def test_owner_can_update(client: AsyncClient, auth_headers: Headers) -> None:
    headers = _organizer(auth_headers)
    gym = await _create_gym(client, headers)
    resp = await client.patch(
        f"/api/v1/gyms/{gym['id']}", headers=headers, json={"name": "Renamed"}
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Renamed"


async def test_other_organizer_cannot_update(client: AsyncClient, auth_headers: Headers) -> None:
    gym = await _create_gym(client, _organizer(auth_headers, "org-A"))
    resp = await client.patch(
        f"/api/v1/gyms/{gym['id']}",
        headers=_organizer(auth_headers, "org-B"),
        json={"name": "Hijacked"},
    )
    assert resp.status_code == 403


async def test_admin_can_override(client: AsyncClient, auth_headers: Headers) -> None:
    gym = await _create_gym(client, _organizer(auth_headers, "org-A"))
    resp = await client.patch(
        f"/api/v1/gyms/{gym['id']}",
        headers=auth_headers(roles=("admin",), sub="adm"),
        json={"name": "AdminEdit"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "AdminEdit"


async def test_soft_delete(client: AsyncClient, auth_headers: Headers) -> None:
    headers = _organizer(auth_headers)
    gym = await _create_gym(client, headers)
    resp = await client.delete(f"/api/v1/gyms/{gym['id']}", headers=headers)
    assert resp.status_code == 204
    after = await client.get(f"/api/v1/gyms/{gym['id']}", headers=headers)
    assert after.json()["is_active"] is False


async def test_list_visibility(client: AsyncClient, auth_headers: Headers) -> None:
    owner = _organizer(auth_headers, "org-A")
    active = await _create_gym(client, owner, name="Active")
    inactive = await _create_gym(client, owner, name="Inactive")
    await client.delete(f"/api/v1/gyms/{inactive['id']}", headers=owner)

    # A player sees only the active gym (not the other org's inactive one).
    player_list = (
        await client.get("/api/v1/gyms", headers=auth_headers(roles=("player",), sub="p9"))
    ).json()
    names = {g["name"] for g in player_list["items"]}
    assert "Active" in names
    assert "Inactive" not in names

    # The owner sees both (incl. their own inactive gym).
    owner_list = (await client.get("/api/v1/gyms", headers=owner)).json()
    owner_names = {g["name"] for g in owner_list["items"]}
    assert {"Active", "Inactive"} <= owner_names

    # An admin sees both as well.
    admin_list = (
        await client.get("/api/v1/gyms", headers=auth_headers(roles=("admin",), sub="adm"))
    ).json()
    assert {"Active", "Inactive"} <= {g["name"] for g in admin_list["items"]}
    assert active["id"]


# --- courts ------------------------------------------------------------------
async def test_create_and_list_courts(client: AsyncClient, auth_headers: Headers) -> None:
    headers = _organizer(auth_headers)
    gym = await _create_gym(client, headers)
    resp = await client.post(
        f"/api/v1/gyms/{gym['id']}/courts", headers=headers, json={"name": "Court 1"}
    )
    assert resp.status_code == 201
    courts = (await client.get(f"/api/v1/gyms/{gym['id']}/courts", headers=headers)).json()
    assert [c["name"] for c in courts] == ["Court 1"]


async def test_create_court_other_gym_forbidden(client: AsyncClient, auth_headers: Headers) -> None:
    gym = await _create_gym(client, _organizer(auth_headers, "org-A"))
    resp = await client.post(
        f"/api/v1/gyms/{gym['id']}/courts",
        headers=_organizer(auth_headers, "org-B"),
        json={"name": "Sneaky"},
    )
    assert resp.status_code == 403


async def test_update_and_soft_delete_court(client: AsyncClient, auth_headers: Headers) -> None:
    headers = _organizer(auth_headers)
    gym = await _create_gym(client, headers)
    court = (
        await client.post(f"/api/v1/gyms/{gym['id']}/courts", headers=headers, json={"name": "A"})
    ).json()
    patched = await client.patch(
        f"/api/v1/courts/{court['id']}", headers=headers, json={"name": "B"}
    )
    assert patched.status_code == 200
    assert patched.json()["name"] == "B"
    deleted = await client.delete(f"/api/v1/courts/{court['id']}", headers=headers)
    assert deleted.status_code == 204


async def test_create_court_missing_gym_404(client: AsyncClient, auth_headers: Headers) -> None:
    resp = await client.post(
        "/api/v1/gyms/00000000-0000-0000-0000-000000000000/courts",
        headers=_organizer(auth_headers),
        json={"name": "X"},
    )
    assert resp.status_code == 404
