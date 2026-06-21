"""Shared FastAPI dependencies: current claims, current user, RBAC guards.

Object-level authorization (ownership) lives in services; these provide
authentication and coarse RBAC (token realm roles only — never frontend claims).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.security import TokenVerifier, get_token_verifier
from app.db.session import get_db
from app.models.user import UserProfile
from app.schemas.user import TokenClaims
from app.services.user import UserService

bearer_scheme = HTTPBearer(auto_error=False, description="Keycloak access token")


@dataclass
class CurrentUser:
    """The authenticated principal: persisted profile + authoritative token roles."""

    profile: UserProfile
    roles: list[str]

    @property
    def id(self) -> UUID:
        return self.profile.id

    def has_role(self, *roles: str) -> bool:
        return bool(set(roles) & set(self.roles))


async def get_current_claims(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    verifier: TokenVerifier = Depends(get_token_verifier),
) -> TokenClaims:
    if credentials is None or not credentials.credentials:
        raise AuthenticationError("Authentication is required.")
    return verifier.verify(credentials.credentials)


async def get_current_user(
    claims: TokenClaims = Depends(get_current_claims),
    db: AsyncSession = Depends(get_db),
) -> CurrentUser:
    """Resolve (provisioning on first login) the local profile for the token."""
    user = await UserService(db).sync_from_claims(claims)
    # Persist first-login provisioning regardless of the endpoint's own writes.
    await db.commit()
    return CurrentUser(profile=user, roles=claims.roles)


def require_role(*allowed: str) -> Callable[[CurrentUser], Awaitable[CurrentUser]]:
    """Dependency factory enforcing that the token carries one of ``allowed``."""

    async def _guard(current: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not current.has_role(*allowed):
            raise AuthorizationError("You do not have the required role.")
        return current

    return _guard
