"""User-facing schemas: token claims, profile read/update."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.enums import UserRole


class TokenClaims(BaseModel):
    """Validated subset of a Keycloak access token."""

    sub: str
    email: str | None = None
    preferred_username: str | None = None
    name: str | None = None
    # App roles present in the token (realm_access.roles ∩ known roles).
    roles: list[str] = Field(default_factory=list)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    display_name: str
    phone_number: str | None
    default_role: UserRole
    is_active: bool
    # Authoritative roles from the current token (not persisted).
    roles: list[str] = Field(default_factory=list)


class UserUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    phone_number: str | None = Field(default=None, max_length=40)
