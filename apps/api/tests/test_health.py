"""Phase 1 health/readiness endpoint tests."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


async def test_health_returns_ok(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_ready_reports_postgres(client: AsyncClient) -> None:
    """Readiness must report on Postgres; the test DB connection is healthy."""
    resp = await client.get("/api/v1/ready")
    body = resp.json()
    assert "postgres" in body["checks"]
    assert "redis" in body["checks"]
    assert body["checks"]["postgres"] == "ok"
    # Overall status reflects the dependency checks.
    assert resp.status_code in (200, 503)
    if resp.status_code == 200:
        assert body["status"] == "ok"
        assert all(state == "ok" for state in body["checks"].values())


@pytest.mark.parametrize("path", ["/api/v1/health", "/api/v1/ready"])
async def test_health_endpoints_need_no_auth(client: AsyncClient, path: str) -> None:
    """Health endpoints must be reachable without an Authorization header."""
    resp = await client.get(path)
    assert resp.status_code != 401
