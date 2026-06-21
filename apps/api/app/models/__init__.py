"""SQLAlchemy ORM models.

Import every model module here so that ``Base.metadata`` is fully populated for
Alembic autogenerate and for test schema creation. Models are added per phase.
"""

from __future__ import annotations

from app.models.audit import AuditEvent
from app.models.gym import Court, Gym
from app.models.notification import Notification
from app.models.registration import RunRegistration
from app.models.run import BasketballRun
from app.models.user import UserProfile

__all__ = [
    "AuditEvent",
    "BasketballRun",
    "Court",
    "Gym",
    "Notification",
    "RunRegistration",
    "UserProfile",
]
