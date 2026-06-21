"""Shared domain enumerations (used by both ORM models and Pydantic schemas)."""

from __future__ import annotations

from enum import StrEnum


class UserRole(StrEnum):
    """Application roles. Authoritative roles come from the Keycloak token; the
    value stored on ``UserProfile.default_role`` is an informational default.

    Convention for all domain enums: member name == value, so the stored DB
    string is unambiguous regardless of SQLAlchemy name/value handling."""

    player = "player"
    organizer = "organizer"
    admin = "admin"


class RunStatus(StrEnum):
    """Lifecycle of a basketball run (see docs/DATA_MODEL.md).

    Players see only ``published`` and later states; ``draft`` is organizer-only.
    ``cancelled`` and ``completed`` are terminal.
    """

    draft = "draft"
    published = "published"
    registration_closed = "registration_closed"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class RegistrationStatus(StrEnum):
    """Lifecycle of a player's registration for a run (Phase 5+)."""

    confirmed = "confirmed"
    waitlisted = "waitlisted"
    checked_in = "checked_in"
    cancelled = "cancelled"
    no_show = "no_show"
    completed = "completed"


class NotificationType(StrEnum):
    """In-app notification categories (Phase 6+)."""

    waitlist_promoted = "waitlist_promoted"
    run_cancelled = "run_cancelled"
    time_changed = "time_changed"
    registration_confirmed = "registration_confirmed"
