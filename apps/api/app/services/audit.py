"""Append-only audit logging (see docs/SECURITY.md).

Records organizer/admin and other significant actions. ``metadata`` must contain
only redacted detail (IDs) — never secrets or PII beyond identifiers.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditEvent


class AuditService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def record(
        self,
        *,
        event_type: str,
        entity_type: str,
        entity_id: UUID,
        actor_id: UUID | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            actor_user_id=actor_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            metadata_json=metadata or {},
        )
        self.db.add(event)
        await self.db.flush()
        return event
