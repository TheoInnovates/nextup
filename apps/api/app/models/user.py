"""UserProfile ORM model.

Keycloak owns credentials; this stores the domain profile, synced from token
claims on the first (and every) authenticated request (see docs/DATA_MODEL.md).
"""

from __future__ import annotations

from sqlalchemy import Boolean, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.enums import UserRole


class UserProfile(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "user_profile"

    # Keycloak subject (`sub`) — stable per identity.
    identity_provider_id: Mapped[str] = mapped_column(Text, unique=True, index=True)
    email: Mapped[str] = mapped_column(Text, unique=True, index=True)
    display_name: Mapped[str] = mapped_column(Text)
    phone_number: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Stored as VARCHAR + CHECK (native_enum=False) for migration-friendliness.
    default_role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role", native_enum=False),
        default=UserRole.player,
        server_default=UserRole.player.value,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"<UserProfile {self.email} ({self.default_role})>"
