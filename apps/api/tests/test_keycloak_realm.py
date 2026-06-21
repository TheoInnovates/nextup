"""Static assertions on the Keycloak realm export.

The full browser login flow can't be exercised without a running Keycloak, so
these checks act as a proxy for the integration risks that would otherwise only
surface at runtime — most importantly the **audience mapper** that puts
``nextup-api`` into the access-token ``aud`` (without it, strict audience
validation 401s every real login while unit tests stay green).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REALM_PATH = (
    Path(__file__).resolve().parents[3] / "infrastructure" / "keycloak" / "nextup-realm.json"
)


@pytest.fixture(scope="module")
def realm() -> dict:
    return json.loads(REALM_PATH.read_text())


def _all_protocol_mappers(realm: dict) -> list[dict]:
    mappers: list[dict] = []
    for client in realm.get("clients", []):
        mappers.extend(client.get("protocolMappers", []))
    for scope in realm.get("clientScopes", []):
        mappers.extend(scope.get("protocolMappers", []))
    return mappers


def test_realm_name(realm: dict) -> None:
    assert realm["realm"] == "nextup"
    assert realm["enabled"] is True


def test_app_roles_present(realm: dict) -> None:
    names = {role["name"] for role in realm["roles"]["realm"]}
    assert {"player", "organizer", "admin"} <= names


def test_clients_present(realm: dict) -> None:
    clients = {c["clientId"]: c for c in realm["clients"]}
    assert "nextup-web" in clients
    assert "nextup-api" in clients
    web = clients["nextup-web"]
    assert web["publicClient"] is True
    assert web["standardFlowEnabled"] is True
    assert web["attributes"]["pkce.code.challenge.method"] == "S256"


def test_audience_mapper_includes_api(realm: dict) -> None:
    """An audience mapper must add `nextup-api` to issued access tokens."""
    audience_mappers = [
        m
        for m in _all_protocol_mappers(realm)
        if m.get("protocolMapper") == "oidc-audience-mapper"
        and m.get("config", {}).get("included.client.audience") == "nextup-api"
        and m.get("config", {}).get("access.token.claim") == "true"
    ]
    assert audience_mappers, "missing oidc-audience-mapper for nextup-api"


def test_test_users_have_roles_and_credentials(realm: dict) -> None:
    users = {u["username"]: u for u in realm["users"]}
    expected = {
        "player1": "player",
        "organizer1": "organizer",
        "admin1": "admin",
    }
    for username, role in expected.items():
        assert username in users, f"missing test user {username}"
        user = users[username]
        assert role in user["realmRoles"]
        assert any(c["type"] == "password" for c in user["credentials"])
