# API

Base path: **`/api/v1`**. This is the contract; endpoints are implemented across Phases 1–7.
The running service serves OpenAPI/Swagger at `/docs`.

## Conventions

- **Auth:** all endpoints except health require a valid Keycloak access token
  (`Authorization: Bearer <jwt>`). The backend validates the JWT independently and enforces
  RBAC (`player`/`organizer`/`admin`) plus object-level ownership.
- **Errors:** consistent JSON envelope, e.g.
  `{ "detail": "<safe message>", "code": "<machine_code>" }`. No internal details leaked.
- **Status codes:** `200` ok, `201` created, `204` no content, `400` validation, `401`
  unauthenticated, `403` unauthorized, `404` not found, `409` conflict (e.g. duplicate
  registration / lost final-slot race), `422` request-schema validation.
- **Pagination:** list endpoints accept `?limit=&offset=` and return
  `{ items, total, limit, offset }`.
- **Validation:** request bodies validated by Pydantic; query/path params typed.
- **Time:** all timestamps in responses are UTC (ISO-8601); clients render in the gym timezone.

## Health
| Method & path | Auth | Notes |
| --- | --- | --- |
| `GET /api/v1/health` | none | Liveness. |
| `GET /api/v1/ready` | none | Readiness — verifies Postgres + Redis. |

## Current user
| Method & path | Auth | Notes |
| --- | --- | --- |
| `GET /api/v1/me` | any | Current profile (synced from token). |
| `PATCH /api/v1/me` | any | Update own `display_name`/`phone_number`. |

## Gyms
| Method & path | Auth | Notes |
| --- | --- | --- |
| `GET /api/v1/gyms` | any | List (admin: all; organizer: own + active). |
| `POST /api/v1/gyms` | organizer | Create; caller becomes owner. |
| `GET /api/v1/gyms/{gym_id}` | any | Detail. |
| `PATCH /api/v1/gyms/{gym_id}` | owner/admin | Update. |
| `DELETE /api/v1/gyms/{gym_id}` | owner/admin | Soft-disable (`is_active=false`). |

## Courts
| Method & path | Auth | Notes |
| --- | --- | --- |
| `GET /api/v1/gyms/{gym_id}/courts` | any | List courts for a gym. |
| `POST /api/v1/gyms/{gym_id}/courts` | owner/admin | Create. |
| `PATCH /api/v1/courts/{court_id}` | owner/admin | Update. |
| `DELETE /api/v1/courts/{court_id}` | owner/admin | Soft-disable. |

## Basketball runs
| Method & path | Auth | Notes |
| --- | --- | --- |
| `GET /api/v1/runs` | any | List; players see `published`+ only. |
| `POST /api/v1/runs` | organizer | Create (status `draft`). |
| `GET /api/v1/runs/{run_id}` | any | Detail (drafts: organizer/admin only). |
| `PATCH /api/v1/runs/{run_id}` | owner/admin | Update. |
| `DELETE /api/v1/runs/{run_id}` | owner/admin | Soft-disable. |
| `POST /api/v1/runs/{run_id}/publish` | owner/admin | `draft → published`. |
| `POST /api/v1/runs/{run_id}/cancel` | owner/admin | `→ cancelled`. |
| `POST /api/v1/runs/{run_id}/start` | owner/admin | `→ in_progress`. |
| `POST /api/v1/runs/{run_id}/complete` | owner/admin | `→ completed`. |

Invalid status transitions return `409`.

## Registrations
| Method & path | Auth | Notes |
| --- | --- | --- |
| `POST /api/v1/runs/{run_id}/registrations` | player | Register self; returns confirmed/waitlisted + timing. `409` on duplicate or lost final-slot race. |
| `GET /api/v1/runs/{run_id}/registrations/me` | player | Own registration + status/timing. |
| `DELETE /api/v1/runs/{run_id}/registrations/me` | player | Cancel own (triggers promotion). |
| `DELETE /api/v1/runs/{run_id}/registrations/{registration_id}` | owner/admin | Organizer cancels a player's registration (triggers promotion). |
| `GET /api/v1/runs/{run_id}/roster` | owner/admin | Confirmed + waitlist roster. |
| `POST /api/v1/runs/{run_id}/registrations/{registration_id}/check-in` | owner/admin | Mark checked in. |
| `POST /api/v1/runs/{run_id}/registrations/{registration_id}/no-show` | owner/admin | Mark no-show. |
| `POST /api/v1/runs/{run_id}/registrations/{registration_id}/promote` | owner/admin | Manual promotion. |

## Notifications
| Method & path | Auth | Notes |
| --- | --- | --- |
| `GET /api/v1/notifications` | any | Own notifications (paginated). |
| `POST /api/v1/notifications/{notification_id}/read` | owner | Mark one read. |
| `POST /api/v1/notifications/read-all` | any | Mark all own read. |
