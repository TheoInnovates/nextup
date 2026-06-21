"""User application logic: claim sync and profile updates."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import UserRole
from app.models.user import UserProfile
from app.repositories.user import UserRepository
from app.schemas.user import TokenClaims, UserUpdate

# Highest-privilege role first; the default is informational only.
_ROLE_PRECEDENCE = (UserRole.admin, UserRole.organizer, UserRole.player)


def _default_role(roles: list[str]) -> UserRole:
    for role in _ROLE_PRECEDENCE:
        if role.value in roles:
            return role
    return UserRole.player


def _derive_display_name(claims: TokenClaims) -> str:
    if claims.name:
        return claims.name
    if claims.preferred_username:
        return claims.preferred_username
    if claims.email:
        return claims.email.split("@", 1)[0]
    return "Player"


class UserService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = UserRepository(db)

    async def sync_from_claims(self, claims: TokenClaims) -> UserProfile:
        """Provision/refresh the local profile from token claims (idempotent)."""
        email = claims.email or f"{claims.sub}@users.noreply.nextup.local"
        return await self.repo.upsert_from_identity(
            identity_provider_id=claims.sub,
            email=email,
            display_name=_derive_display_name(claims),
            default_role=_default_role(claims.roles),
        )

    async def update_profile(self, user: UserProfile, data: UserUpdate) -> UserProfile:
        if data.display_name is not None:
            user.display_name = data.display_name
        if data.phone_number is not None:
            user.phone_number = data.phone_number
        await self.db.flush()
        return user
