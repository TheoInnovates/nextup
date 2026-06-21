"""/me endpoint + claim-sync + RBAC guard tests."""

from __future__ import annotations

from collections.abc import Callable

import pytest
from app.core.dependencies import CurrentUser, require_role
from app.core.exceptions import AuthorizationError
from app.models.user import UserProfile
from httpx import AsyncClient


async def test_me_requires_auth(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/me")
    assert resp.status_code == 401
    assert resp.json()["code"] == "unauthenticated"


async def test_me_provisions_profile_on_first_call(
    client: AsyncClient, auth_headers: Callable[..., dict[str, str]]
) -> None:
    headers = auth_headers(roles=("player",), sub="kc-1", email="p1@example.com", name="Pat")
    resp = await client.get("/api/v1/me", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "p1@example.com"
    assert body["display_name"] == "Pat"
    assert body["default_role"] == "player"
    assert body["roles"] == ["player"]


async def test_me_is_idempotent(
    client: AsyncClient, auth_headers: Callable[..., dict[str, str]]
) -> None:
    headers = auth_headers(roles=("player",), sub="kc-2", email="p2@example.com")
    first = (await client.get("/api/v1/me", headers=headers)).json()
    second = (await client.get("/api/v1/me", headers=headers)).json()
    assert first["id"] == second["id"]


async def test_default_role_uses_precedence(
    client: AsyncClient, auth_headers: Callable[..., dict[str, str]]
) -> None:
    headers = auth_headers(roles=("player", "organizer"), sub="kc-3", email="o1@example.com")
    body = (await client.get("/api/v1/me", headers=headers)).json()
    assert body["default_role"] == "organizer"
    assert set(body["roles"]) == {"player", "organizer"}


async def test_patch_me_updates_allowed_fields(
    client: AsyncClient, auth_headers: Callable[..., dict[str, str]]
) -> None:
    headers = auth_headers(roles=("player",), sub="kc-4", email="p4@example.com")
    await client.get("/api/v1/me", headers=headers)
    resp = await client.patch(
        "/api/v1/me",
        headers=headers,
        json={"display_name": "New Name", "phone_number": "+1 555 0100"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["display_name"] == "New Name"
    assert body["phone_number"] == "+1 555 0100"


async def test_patch_me_rejects_too_long_display_name(
    client: AsyncClient, auth_headers: Callable[..., dict[str, str]]
) -> None:
    headers = auth_headers(roles=("player",), sub="kc-5", email="p5@example.com")
    await client.get("/api/v1/me", headers=headers)
    resp = await client.patch("/api/v1/me", headers=headers, json={"display_name": "x" * 200})
    assert resp.status_code == 422


# --- RBAC guard (unit) -------------------------------------------------------
async def test_require_role_allows_matching_role() -> None:
    guard = require_role("organizer", "admin")
    current = CurrentUser(profile=UserProfile(), roles=["organizer"])
    assert await guard(current=current) is current


async def test_require_role_blocks_missing_role() -> None:
    guard = require_role("organizer", "admin")
    current = CurrentUser(profile=UserProfile(), roles=["player"])
    with pytest.raises(AuthorizationError):
        await guard(current=current)
