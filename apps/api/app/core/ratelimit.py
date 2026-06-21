"""Lightweight Redis-backed rate limiting for sensitive endpoints.

A fixed-window counter keyed by (scope, user). Applied to registration (a
sensitive, abuse-prone action). The dependency is overridable in tests so the
suite doesn't depend on Redis fixed-window state across cases.
"""

from __future__ import annotations

import redis.asyncio as redis
from fastapi import Depends

from app.core.config import get_settings
from app.core.dependencies import CurrentUser, get_current_user
from app.core.exceptions import AppError

# Registration limit: generous for real use, low enough to blunt abuse.
REGISTER_LIMIT = 20
REGISTER_WINDOW_SECONDS = 60

_client: redis.Redis | None = None


class RateLimitError(AppError):
    status_code = 429
    code = "rate_limited"
    message = "Too many requests. Please slow down."


def _redis() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.from_url(get_settings().redis_url)
    return _client


async def _enforce(*, scope: str, user_id: str, times: int, seconds: int) -> None:
    client = _redis()
    key = f"ratelimit:{scope}:{user_id}"
    count = await client.incr(key)
    if count == 1:
        await client.expire(key, seconds)
    if count > times:
        raise RateLimitError()


async def registration_rate_limit(
    current: CurrentUser = Depends(get_current_user),
) -> None:
    """FastAPI dependency: rate-limit registration attempts per user."""
    await _enforce(
        scope="register",
        user_id=str(current.id),
        times=REGISTER_LIMIT,
        seconds=REGISTER_WINDOW_SECONDS,
    )
