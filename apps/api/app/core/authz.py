"""Shared object-level authorization helpers.

RBAC (role gating) happens at the route edge via ``require_role``; these helpers
enforce ownership inside services (organizer may act only on their own resources;
admin overrides).
"""

from __future__ import annotations

from uuid import UUID

from app.core.dependencies import CurrentUser
from app.core.exceptions import AuthorizationError
from app.enums import UserRole


def assert_can_manage(
    owner_id: UUID, user: CurrentUser, message: str = "You are not authorized."
) -> None:
    if user.has_role(UserRole.admin) or owner_id == user.id:
        return
    raise AuthorizationError(message)
