"""Version 1 API router aggregation."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import (
    gyms,
    health,
    notifications,
    registrations,
    roster,
    runs,
    users,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(users.router)
api_router.include_router(gyms.router)
api_router.include_router(runs.router)
api_router.include_router(registrations.router)
api_router.include_router(roster.router)
api_router.include_router(notifications.router)
