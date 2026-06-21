"""Custom Prometheus metrics (HTTP request/latency metrics come from the
prometheus-fastapi-instrumentator; these are domain counters)."""

from __future__ import annotations

from prometheus_client import Counter

registrations_total = Counter(
    "nextup_registrations_total",
    "Run registrations created, by assignment result.",
    ["result"],
)
promotions_total = Counter(
    "nextup_promotions_total",
    "Waitlist promotions performed.",
)
checkins_total = Counter(
    "nextup_checkins_total",
    "Player check-ins recorded.",
)
task_failures_total = Counter(
    "nextup_task_failures_total",
    "Background (Celery) task failures.",
    ["task"],
)
