"""Liveness and readiness endpoints (unauthenticated).

``/health`` is a pure liveness probe. ``/ready`` verifies the critical
dependencies (PostgreSQL + Redis) and returns 503 if any check fails so that
orchestrators do not route traffic to an unready instance.
"""

from __future__ import annotations

import redis.asyncio as redis
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.session import get_db
from app.schemas.common import HealthResponse, ReadyResponse

router = APIRouter(tags=["health"])
log = get_logger(__name__)


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Liveness: the process is up and serving."""
    return HealthResponse(status="ok")


@router.get("/ready", response_model=ReadyResponse)
async def ready(response: Response, db: AsyncSession = Depends(get_db)) -> ReadyResponse:
    """Readiness: verify PostgreSQL and Redis connectivity."""
    checks: dict[str, str] = {}

    try:
        await db.execute(text("SELECT 1"))
        checks["postgres"] = "ok"
    except Exception:
        log.warning("readiness.postgres_unavailable", exc_info=True)
        checks["postgres"] = "error"

    settings = get_settings()
    client = redis.from_url(settings.redis_url)
    try:
        await client.ping()
        checks["redis"] = "ok"
    except Exception:
        log.warning("readiness.redis_unavailable", exc_info=True)
        checks["redis"] = "error"
    finally:
        await client.aclose()

    healthy = all(state == "ok" for state in checks.values())
    if not healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadyResponse(status="ok" if healthy else "degraded", checks=checks)
