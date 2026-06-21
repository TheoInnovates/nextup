# Architecture

## Overview

NextUp is a **modular monolith**: a single FastAPI backend (organized into layers and
domain modules) plus a Next.js frontend, fronted by Caddy, backed by PostgreSQL and Redis,
with Celery for async work and Keycloak for identity. Excluded MVP features (payments,
ratings, native apps — spec §4) are kept out, but the layering leaves room to add them
without a redesign.

## Logical diagram

```text
Browser
   |
   v
Caddy  (TLS termination, reverse proxy, label-driven routing)
   |
   +-----------------------------+
   |                             |
   v                             v
Next.js Frontend            FastAPI Backend
 (public OIDC client,           |
  Auth Code + PKCE)   +---------+----------+-----------+
                      |         |          |           |
                      v         v          v           v
                 PostgreSQL   Redis     Celery     Prometheus
                                |        worker      (metrics)
                                v          |
                            cache /        v
                           queue state  background tasks
                                        (notifications, etc.)

Authentication:
Browser -> Keycloak (auth.nextup.local) -> Access Token (JWT)
        -> FastAPI validates signature/issuer/audience via realm JWKS
```

## Components and responsibilities

| Component        | Responsibility |
| ---------------- | -------------- |
| **Caddy**        | TLS termination (mkcert `*.local`), reverse proxy. Routing is label-driven via `caddy-docker-proxy`; each service self-registers with `caddy.*` labels. Exposes metrics for Prometheus. |
| **Next.js web**  | UI for players/organizers/admins. Public OIDC client (Auth Code + PKCE). Calls the API with the bearer token. Renders loading/empty/error states; never the authority on roles/ownership. |
| **FastAPI api**  | The source of truth. Validates JWTs, enforces RBAC + object-level authorization, runs business logic and the scheduling engine, owns the database. |
| **PostgreSQL**   | Persistent application data. UUID primary keys. All timestamps stored in UTC. |
| **Redis**        | Caching, Celery broker/result backend, and queue/lock support. |
| **Celery worker**| Async tasks (e.g. dispatching notifications, future email sends). Kept off the request path. |
| **Keycloak**     | Identity provider. Owns credentials. Realm `nextup`, roles `player`/`organizer`/`admin`. |
| **Mailpit**      | Captures outbound email locally for inspection. |
| **Prometheus/Grafana** | Metrics scraping and dashboards (Phase 8). |

## Backend layering

Business logic stays **out of route handlers** (spec §6):

```
api/          FastAPI routers — thin: parse/validate input, call a service, shape the response
services/     application/business logic; orchestrates repositories within a transaction
repositories/ isolated data access (SQLAlchemy queries); no business rules
scheduling/   deterministic scheduling engine — pure, HTTP-free, unit-tested in isolation
models/       SQLAlchemy ORM models (persistence)
schemas/      Pydantic request/response models (API contract) — distinct from ORM models
core/         config, security (JWT validation), logging, exceptions, dependencies
db/           engine/session, base metadata
workers/      Celery app + task definitions
```

Dependency injection (FastAPI `Depends`) provides the DB session, the current authenticated
user, and authorization guards to handlers.

## Request & auth flow

1. The browser obtains an access token from Keycloak via Authorization Code + PKCE.
2. It calls `https://api.nextup.local/api/v1/...` with `Authorization: Bearer <jwt>`.
3. The backend validates the JWT signature against the realm JWKS and checks `iss`/`aud`/`exp`.
   Because both the browser and backend reach Keycloak through the same host
   (`auth.nextup.local` via Caddy), the **issuer matches on both sides** — set
   `KC_HOSTNAME=auth.nextup.local`.
4. A dependency resolves/synchronizes the local `UserProfile` from token claims.
5. RBAC (realm roles) and object-level checks (ownership) authorize the action.
6. The handler delegates to a service; the service uses repositories within a transaction.

## Concurrency & transactions

Registration and waitlist promotion are the correctness-critical paths. Each runs in a
**single database transaction** that locks the relevant run's capacity/registration rows
(`SELECT … FOR UPDATE`) before counting confirmed registrations, so two players cannot both
claim the final slot. Promotion (cancel → pick earliest eligible waitlisted player → promote →
recompute queue → notify) is likewise atomic. Concurrency tests cover the final-slot race and
promotion (spec §9, §15).

## Time handling

All timestamps are stored in UTC. Each gym has a configured timezone; arrival and play times
are computed in UTC and converted to the gym timezone for display. The scheduling formula
(see `docs/DATA_MODEL.md`) is deterministic and unit-tested.

## Key decisions (ADR-style)

- **Modular monolith, not microservices** (spec §5): simplest production-capable shape for the MVP.
- **Keycloak public client + PKCE** for the SPA; backend validates JWTs independently — no client
  secret in the browser, backend never trusts the frontend.
- **Label-driven Caddy + mkcert `*.local`**: matches the established infra convention
  (`project-4-workspace`) and lets services self-register routes.
- **Celery + Redis for async** so notification dispatch and future email/SMS work stay off the
  request path.
- **UUID primary keys** for application entities (spec §8): non-enumerable, merge-friendly.
- **GitLab CI** (`gitlab.devhub.ninja/theo/project-6-nextup`) per spec §17.

## Deployment

Local: Docker Compose (`make up`). The compose file declares the full stack; application
services come online starting Phase 1. A real deployment target is selected later — the
GitLab CI `deploy` stage is a manual placeholder until then.
