# Data Model

All application entities use **UUID** primary keys. All timestamps are stored in **UTC**
(`timestamptz`); display converts to the gym's timezone. `created_at`/`updated_at` are
audit columns on every mutable entity.

## Entity-relationship overview

```text
UserProfile 1───* Gym (owner)
Gym         1───* Court
Gym         1───* BasketballRun
UserProfile 1───* BasketballRun (organizer)
BasketballRun 1─* RunRegistration *───1 UserProfile (player)
UserProfile 1───* Notification *───0..1 BasketballRun (related_run)
(any entity) ──* AuditEvent (actor_user_id, entity_type, entity_id)
```

## UserProfile

The identity provider (Keycloak) owns credentials; the app stores the domain profile,
synchronized from token claims on first authenticated request.

| Field | Type | Notes |
| ----- | ---- | ----- |
| `id` | UUID | PK |
| `identity_provider_id` | text | Keycloak `sub`; unique |
| `email` | text | unique |
| `display_name` | text | |
| `phone_number` | text? | optional |
| `default_role` | enum(`player`,`organizer`,`admin`) | informational default; authoritative roles come from the token |
| `is_active` | bool | |
| `created_at` / `updated_at` | timestamptz | |

## Gym

| Field | Type | Notes |
| ----- | ---- | ----- |
| `id` | UUID | PK |
| `name` | text | |
| `description` | text | |
| `address_line_1` | text | |
| `address_line_2` | text? | optional |
| `city` / `state` / `postal_code` | text | |
| `timezone` | text | IANA tz (e.g. `America/New_York`); drives display |
| `owner_user_id` | UUID | FK → UserProfile |
| `is_active` | bool | |
| `created_at` / `updated_at` | timestamptz | |

## Court

| Field | Type | Notes |
| ----- | ---- | ----- |
| `id` | UUID | PK |
| `gym_id` | UUID | FK → Gym |
| `name` | text | |
| `is_active` | bool | |
| `created_at` / `updated_at` | timestamptz | |

## BasketballRun

| Field | Type | Notes |
| ----- | ---- | ----- |
| `id` | UUID | PK |
| `gym_id` | UUID | FK → Gym |
| `organizer_user_id` | UUID | FK → UserProfile |
| `title` | text | |
| `description` | text? | optional |
| `start_time` / `end_time` | timestamptz | UTC |
| `registration_opens_at` / `registration_closes_at` | timestamptz | |
| `cancellation_deadline` | timestamptz | |
| `maximum_players` | int | capacity of confirmed slots |
| `players_per_team` | int | |
| `number_of_courts` | int | |
| `estimated_game_minutes` | int | game block length |
| `arrival_lead_minutes` | int | arrive-before-play buffer |
| `status` | enum | see below |
| `created_at` / `updated_at` | timestamptz | |

**Run status:** `draft` → `published` → `registration_closed` → `in_progress` →
`completed`; `cancelled` reachable from any non-terminal state. Players see only
`published`+ runs; `draft` is organizer-only. Invalid transitions are rejected by the
status machine (Phase 4).

## RunRegistration

| Field | Type | Notes |
| ----- | ---- | ----- |
| `id` | UUID | PK |
| `run_id` | UUID | FK → BasketballRun |
| `player_user_id` | UUID | FK → UserProfile |
| `status` | enum | see below |
| `queue_position` | int? | deterministic; waitlist ordering |
| `assigned_slot_number` | int? | confirmed slot index |
| `assigned_arrival_time` | timestamptz? | computed |
| `estimated_play_time` | timestamptz? | computed |
| `registered_at` | timestamptz | |
| `cancelled_at` | timestamptz? | |
| `checked_in_at` | timestamptz? | |
| `created_at` / `updated_at` | timestamptz | |

**Registration status:** `confirmed`, `waitlisted`, `checked_in`, `cancelled`,
`no_show`, `completed`.

**Constraints:**
- At most **one active registration per (run, player)** — enforced with a partial unique
  index over active statuses (`confirmed`, `waitlisted`, `checked_in`), so a player may
  re-register after cancelling while cancelled rows are retained for audit.
- Queue positions are deterministic (ordered by `registered_at`, tie-broken by `id`).
- Cancelled/no-show rows are never deleted — retained for audit.

## Notification

| Field | Type | Notes |
| ----- | ---- | ----- |
| `id` | UUID | PK |
| `user_id` | UUID | FK → UserProfile (recipient) |
| `type` | text/enum | e.g. `waitlist_promoted`, `time_changed`, `run_cancelled` |
| `title` | text | |
| `message` | text | |
| `related_run_id` | UUID? | FK → BasketballRun, optional |
| `is_read` | bool | |
| `created_at` | timestamptz | |
| `read_at` | timestamptz? | |

## AuditEvent

Append-only record of organizer/admin (and other significant) actions.

| Field | Type | Notes |
| ----- | ---- | ----- |
| `id` | UUID | PK |
| `actor_user_id` | UUID? | optional (system events) |
| `event_type` | text | e.g. `registration.promoted`, `run.published` |
| `entity_type` | text | e.g. `BasketballRun`, `RunRegistration` |
| `entity_id` | UUID | affected entity |
| `metadata_json` | jsonb | redacted contextual detail (no secrets/PII beyond IDs) |
| `created_at` | timestamptz | |

## Scheduling formula (deterministic — spec §9)

```text
players_per_game   = players_per_team * 2 * number_of_courts
game_block         = estimated_game_minutes
slot_number        = floor(confirmed_position / players_per_game)     # confirmed_position is 0-based
estimated_play_time     = run.start_time + slot_number * game_block (minutes)
assigned_arrival_time   = estimated_play_time - arrival_lead_minutes
```

**Invariants** (unit-tested, Phase 5):
- Deterministic for a given input.
- Arrival time may precede `start_time` (it represents when to show up); **play time** never does.
- A play time computed past `end_time` flags a capacity problem rather than silently scheduling it.
- Accounts for multiple courts and player capacity via `players_per_game`.

`confirmed_position` is the 0-based index of the registration among active confirmed
registrations ordered by `registered_at`. On cancellation+promotion, positions and the
derived times are recomputed within the same transaction (Phase 6).
