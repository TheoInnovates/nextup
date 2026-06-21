"""Phase 8: metrics endpoint, security headers, request correlation, rate limit."""

from __future__ import annotations

import uuid

import pytest
from app.core.ratelimit import RateLimitError, _enforce
from app.main import app as prod_app
from httpx import ASGITransport, AsyncClient


async def test_metrics_endpoint_exposed() -> None:
    transport = ASGITransport(app=prod_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        resp = await ac.get("/metrics")
    assert resp.status_code == 200
    body = resp.text
    assert "# HELP" in body
    # Unlabeled custom counters are exported immediately at 0.
    assert "nextup_promotions_total" in body


async def test_security_headers_present(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/health")
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert resp.headers["Referrer-Policy"] == "no-referrer"


async def test_request_id_echoed(client: AsyncClient) -> None:
    # Generated when absent...
    resp = await client.get("/api/v1/health")
    assert resp.headers.get("X-Request-ID")
    # ...and echoed when supplied.
    supplied = "test-request-id-123"
    resp2 = await client.get("/api/v1/health", headers={"X-Request-ID": supplied})
    assert resp2.headers["X-Request-ID"] == supplied


async def test_rate_limiter_blocks_after_limit() -> None:
    scope = f"test-{uuid.uuid4().hex}"
    await _enforce(scope=scope, user_id="u1", times=2, seconds=60)
    await _enforce(scope=scope, user_id="u1", times=2, seconds=60)
    with pytest.raises(RateLimitError):
        await _enforce(scope=scope, user_id="u1", times=2, seconds=60)
