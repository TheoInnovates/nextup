# CLAUDE.md — NextUp

Guidance for working in this repository. Keep this file in sync with the code.

## What NextUp is

A basketball-run scheduling platform. Players register for organized runs at gyms
and are told **whether they're confirmed or waitlisted, when to arrive, and when
they're expected to play** — instead of waiting at a gym blindly. Organizers create
gyms and runs, manage capacity, and run check-in. See `docs/` for the full spec.

## Tech stack

- **Frontend:** Next.js, TypeScript (strict), React, Tailwind, React Hook Form, Zod, TanStack Query.
- **Backend:** Python, FastAPI, SQLAlchemy 2, Alembic, Pydantic, PostgreSQL.
- **Auth:** Keycloak (OIDC). Web is a public client (Auth Code + PKCE); the backend
  validates JWTs independently against the realm JWKS.
- **Async:** Celery + Redis. **Proxy:** Caddy (label-driven). **Email:** Mailpit.
- **Observability:** Prometheus + Grafana, structured JSON logs.

## Repository map

```
apps/web/                 Next.js app (app/, components/, features/, hooks/, lib/, tests/)
apps/api/app/             FastAPI: api/ core/ db/ models/ schemas/ services/ repositories/ scheduling/ workers/
apps/api/{alembic,tests}/ migrations and pytest suite
infrastructure/           caddy/ keycloak/ prometheus/ grafana/ docker/
docs/                     ARCHITECTURE, IMPLEMENTATION_PLAN, TASKS, DATA_MODEL, API, SECURITY, RUNBOOK
scripts/                  setup.sh and operational scripts
docker-compose.yml        full local stack    Makefile  .env.example  .gitlab-ci.yml
```

## Commands

```bash
make setup     # bootstrap .env + mkcert TLS certs
make up        # start the stack (services land starting Phase 1)
make down      # stop;  make logs s=api  to tail one service
make migrate   # Alembic (Phase 1+)
make seed      # dev seed data (Phase 9)
make test      # test-api + test-web
make lint format
make validate  # docker compose config --quiet
```

## Conventions (non-negotiable)

- **Backend is the source of truth.** Never trust role/ownership claims from the frontend.
  Do not duplicate business rules across web and api.
- **Layering:** thin route handlers → services (business logic) → repositories (data access).
  Keep the scheduling engine separate from HTTP handling. SQLAlchemy models ≠ Pydantic schemas.
- **Time:** store all timestamps in **UTC**; display in the gym's configured timezone.
- **Concurrency:** registration and waitlist promotion run in a single DB transaction with
  row locks (`SELECT … FOR UPDATE`) so two players can't claim the final slot.
- **Auth:** RBAC (`player`/`organizer`/`admin`) plus object-level checks — organizers only touch
  their own gyms/runs, players only their own registrations, admin overrides.
- **Python:** explicit type hints, Ruff lint/format, mypy, custom domain exceptions, no broad excepts.
- **TypeScript:** strict mode, no `any`, Zod for runtime validation, handle loading/error/empty states.
- **Secrets:** never commit them. `.env` is gitignored; `.env.example` holds `CHANGE_ME_` placeholders.

## Working process (per spec §22)

Implement the smallest functional vertical slice, run its tests, fix failures before
continuing, keep docs synchronized, avoid unrelated refactoring, keep the app deployable
after every phase. Do not mark a task done on code generation alone — see `docs/TASKS.md`
and the Definition of Done. Update `docs/TASKS.md` as work progresses.

## Status

**Phases 1–9 implemented** (see `docs/TASKS.md` for per-item status + verification notes and
`docs/RELEASE_NOTES.md`): auth/users, gyms/courts (ownership/IDOR), runs (status machine +
lifecycle + tz), registration with the deterministic **scheduling engine** + final-slot
concurrency safety, cancellation + atomic waitlist promotion + notifications + audit, roster
+ check-in, observability/hardening (metrics, request-id logging, rate limits, security
headers, CI scans), and the dev seed + Playwright E2E specs.

Backend: **92 tests** (incl. scheduling-engine units, status machine, RBAC/IDOR, and **two
real concurrent-transaction tests** — registration final-slot + atomic promotion). Web:
**81+ vitest**. Migrations `0001→0005` reversible. **Verification ceiling:** the live stack
over Caddy HTTPS + browser-OIDC login and the Playwright E2E aren't runnable in this sandbox
(`mkcert` absent, ports 80/443 bound) — those items are marked `[~]`, with the realm-JSON
audience test + per-piece checks as proxies.

Backend tests need a real Postgres: run `make test-api` (auto-provisions a throwaway DB) or
set `TEST_DATABASE_URL` and run `uv run pytest` in `apps/api`. The host `npm` is broken in
this environment; run web tooling via `node:22` Docker (see CI/Makefile patterns).

**Auth patterns to reuse (Phases 3+):** backend route guards via `Depends(require_role("organizer"))`
and `Depends(get_current_user)` (returns `CurrentUser{profile, roles}`); object-level
ownership checks live in services, not handlers. Domain enums use `StrEnum` with member
name == value. Web data access goes through `apiFetch(path, zodSchema, init?)` which attaches
the bearer token automatically.
