"""Data access for UserProfile."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import UserRole
from app.models.user import UserProfile


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, user_id: UUID) -> UserProfile | None:
        return await self.db.get(UserProfile, user_id)

    async def get_by_identity(self, identity_provider_id: str) -> UserProfile | None:
        return await self.db.scalar(
            select(UserProfile).where(UserProfile.identity_provider_id == identity_provider_id)
        )

    async def upsert_from_identity(
        self,
        *,
        identity_provider_id: str,
        email: str,
        display_name: str,
        default_role: UserRole,
    ) -> UserProfile:
        """Race-safe provision: INSERT … ON CONFLICT DO UPDATE on the unique
        identity, then return the (now guaranteed-present) ORM row.

        Two concurrent first-logins serialise on the unique-index row lock, so no
        duplicate profile is created and both callers observe the row.
        """
        stmt = (
            pg_insert(UserProfile)
            .values(
                identity_provider_id=identity_provider_id,
                email=email,
                display_name=display_name,
                default_role=default_role.value,
            )
            .on_conflict_do_update(
                index_elements=[UserProfile.identity_provider_id],
                set_={"email": email, "display_name": display_name},
            )
        )
        await self.db.execute(stmt)
        await self.db.flush()
        user = await self.get_by_identity(identity_provider_id)
        assert user is not None  # guaranteed by the upsert
        return user
