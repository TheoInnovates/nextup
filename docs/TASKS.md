# Tasks

Legend: `[ ]` not started · `[~]` in progress · `[x]` completed · `[!]` blocked

A task is complete only per the Definition of Done (spec §20): works, tested, type-checked,
linted, documented, migrated, authorized, error-handled, no secrets committed, runs under
Docker Compose, CI passes.

## Phase 0 — Repository & documentation
- [x] Repository directory structure (spec §7)
- [x] `CLAUDE.md`
- [x] `README.md`
- [x] `docs/ARCHITECTURE.md`
- [x] `docs/IMPLEMENTATION_PLAN.md`
- [x] `docs/TASKS.md`
- [x] `docs/DATA_MODEL.md`
- [x] `docs/API.md`
- [x] `docs/SECURITY.md`
- [x] `docs/RUNBOOK.md` (skeleton; expanded in Phase 8)
- [x] `.env.example`
- [x] `Makefile`
- [x] Starter `docker-compose.yml` (validates via `docker compose config`)
- [x] `.gitignore`, `.gitlab-ci.yml` skeleton, Caddy base config, infra placeholders
- [x] `docker compose config --quiet` passes
- [x] Docs cross-checked against spec §8/§10

## Phase 1 — Infrastructure & service scaffolding
- [x] FastAPI scaffold + `GET /api/v1/health`, `GET /api/v1/ready` (ready checks PG + Redis)
- [x] Next.js scaffold calling the API health endpoint (TanStack Query, loading/error/ready states)
- [x] PostgreSQL + Redis connections (async SQLAlchemy engine; redis.asyncio)
- [x] Alembic configured (async env.py, `alembic upgrade head` runs clean)
- [x] Keycloak + Caddy wired into the stack (declared + label-routed in compose; `compose config` validates)
- [x] Structured JSON logging (structlog; uvicorn logs also rendered as JSON)
- [x] Dockerfiles (`apps/api`, `apps/web`); both build + run as **non-root** (`appuser`/`nextjs`)
- [x] Basic CI jobs (lint/typecheck/test/build) defined in `.gitlab-ci.yml`
- [~] `make up` brings the whole stack healthy — see verification note

### Phase 1 verification notes
Verified by running locally: backend `ruff`/`mypy`/`pytest` (4 passed against a real
Postgres + Redis), uvicorn serves JSON-logged HTTP; frontend `eslint`/`tsc`/`vitest`
(3 passed) + `next build` (standalone); both Docker images build and serve
(`/api/v1/health` → ok; web `/` → 200) as non-root; `docker compose config` validates;
`make test-api` green. **Not live-verifiable in this sandbox:** the full `make up`
over Caddy HTTPS (`mkcert` is absent and host ports 80/443 are bound), and GitLab
runner execution. CI job *commands* mirror the locally-passing ones.

## Phase 2 — Authentication & users
- [x] Keycloak realm import: roles, clients (incl. `nextup-api` audience mapper), test users
- [x] Backend JWT validation (JWKS, iss/aud/exp; injectable verifier)
- [x] `UserProfile` model + migration (`0001`) + race-safe claim sync (upsert)
- [x] `GET /api/v1/me`, `PATCH /api/v1/me`
- [x] Frontend login (Auth Code + PKCE via react-oidc-context; token-attach seam + callback)
- [x] Role-protected routes (frontend `RoleGate`, UX-only) + RBAC guards (backend `require_role`)
- [x] Auth + authorization tests (23 backend, incl. realm-JSON audience assertion; 10 web)

### Phase 2 verification notes
Verified by running: backend `ruff`/`mypy`/`pytest` (23 passed — token signature/iss/aud/exp,
role filtering, `/me` provisioning+idempotency+RBAC, realm audience mapper) and the migration
upgrade/downgrade/upgrade cycle; frontend `eslint`/`tsc`/`vitest` (10 passed — token-attach
seam + role parsing) and `next build`. **Not live-verifiable here:** the actual browser
login/redirect against a running Keycloak (`[~]`); the realm-JSON audience-mapper test is the
static proxy that guards the most likely integration failure (missing `nextup-api` in `aud`).

## Phase 3 — Gym & court management
- [x] Gym + Court models + migration (`0002`)
- [x] Gym API (CRUD) + Court API (CRUD)
- [x] Ownership controls (organizer owns; admin overrides) — enforced in services
- [x] Organizer gym pages (list, create, detail + courts manager; RoleGate-gated controls)
- [x] Tests (ownership/IDOR, CRUD, visibility, validation; 16 backend + 12 web)

## Phase 4 — Basketball-run management
- [x] Run model + migration (`0003`)
- [x] Run status machine (pure, separately tested; invalid transitions → 409)
- [x] publish/cancel/start/complete actions; create/edit run (backend)
- [x] Create/edit run forms + upcoming-run list + run-details page (frontend; gym-tz display)
- [x] Timezone handling (UTC store via `timestamptz`; gym-tz display is frontend)
- [x] Backend tests (transitions, visibility, validation, ownership) — see notes

### Phase 4 verification notes
Backend verified by running: `ruff`/`mypy` clean; `pytest` (53 → 63 with the scheduling
engine) covering create/authz, draft visibility, full lifecycle, invalid-transition 409,
ownership 403, admin override, time-window validation; migration chain `0001→0003` upgrades
and downgrades cleanly. **Pending:** the run frontend pages (list/detail/forms with gym-tz
display) — to be built like the Phase 3 organizer pages.

## Phase 5 — Registration & scheduling engine
- [x] RunRegistration model + migration (`0004`, partial unique index over active statuses)
- [x] Scheduling engine (pure, deterministic) + 10 unit tests
- [x] Capacity controls + confirmed/waitlist assignment (run-row `FOR UPDATE` lock)
- [x] Arrival + estimated play-time calculation (from the engine)
- [x] Duplicate-registration protection (active-check + partial unique index backstop → 409)
- [x] Player registration page (frontend; confirmed/waitlist status + gym-tz timing)
- [x] Concurrency test: final available slot (real concurrent transactions; self-proving)

### Phase 5 verification notes
Backend verified by running: `ruff`/`mypy` clean; `pytest` (71 passed). The final-slot
**race test uses two genuinely concurrent transactions** that COMMIT (its own engine,
`TRUNCATE` cleanup) — and is **self-proving**: removing the `FOR UPDATE` lock makes it fail
with two `confirmed` (over-capacity), restoring it makes it pass. Migration chain `0001→0004`
upgrades/downgrades cleanly. **Pending:** the player registration page (frontend).

## Phase 6 — Cancellation & waitlist promotion
- [x] Player + organizer cancellation (`DELETE …/me`, `DELETE …/{id}`) + manual promote
- [x] Automatic promotion (earliest eligible) + deterministic queue/slot recalculation
- [x] In-app Notification creation (`waitlist_promoted`) + GET/read endpoints
- [x] AuditEvent recording (`registration.cancelled` / `.promoted`)
- [x] Single-transaction guarantee + concurrency tests (atomic under run-row lock)
- [x] Notifications page + cancel-registration button (frontend)

### Phase 6 verification notes
Backend verified by running: `ruff`/`mypy` clean; `pytest` (80 passed) covering promotion,
queue recompute, notification + audit creation, manual promote (incl. `run_full` 409),
re-register after cancel, and a **concurrent-cancellation test** (two confirmed cancel at
once → waitlister promoted exactly once, capacity invariant holds). Migration chain
`0001→0005` up/down cleanly.

## Phase 7 — Roster & check-in
- [x] Organizer roster + waitlist view (`GET /runs/{id}/roster` with player info)
- [x] Check-in + no-show actions (status changes + audit)
- [x] Run start/complete controls (Phase 4 lifecycle endpoints)
- [x] Mobile-friendly check-in screen (`/runs/[id]/roster`, large tap targets)
- [x] Tests (attendance authz 403, check-in/no-show status changes; 6 backend + web)

## Phase 8 — Observability & production hardening
- [x] Prometheus metrics (HTTP via instrumentator + `nextup_registrations/promotions/checkins/task_failures`)
- [x] Grafana dashboard (provisioned datasource + NextUp Overview dashboard)
- [x] Request-correlation logging (`X-Request-ID` + structlog contextvars)
- [x] Rate limits on sensitive endpoints (registration; Redis fixed window → 429)
- [x] Security headers + CORS restrictions (middleware; CORS to configured origins)
- [x] Dependency + container scans in CI (pip-audit, npm audit, Trivy — `allow_failure`)
- [x] `docs/RUNBOOK.md` expanded (observability + hardening sections)

### Phase 8 verification notes
Backend verified by running: `ruff`/`mypy` clean; `pytest` (90 passed — `/metrics` exposed,
security headers present, request-id generated+echoed, rate limiter blocks after the limit).
Prometheus/Grafana config + Grafana dashboard JSON validated structurally; API image rebuilds
with the new dependency. **Not live-verifiable here:** scraping/dashboards in a running
Grafana, and CI scan jobs on a GitLab runner.

## Phase 9 — End-to-end validation
- [x] Seed command (spec §19 data) — `make seed` / `python -m app.seed`, idempotent, tested
- [~] Playwright Scenario 1: confirmed registration (spec written; needs live stack)
- [~] Playwright Scenario 2: waitlist promotion + notification (spec written; needs live stack)
- [~] Playwright Scenario 3: check-in (spec written; needs live stack)
- [x] Final README, API docs, demo instructions
- [x] Known limitations + release notes (`docs/RELEASE_NOTES.md`)
- [~] Clean-checkout startup verified — see note

### Phase 9 verification notes
Seed verified by running (`python -m app.seed` → 5 users / 1 gym / 3 runs / 3 registrations,
idempotent on re-run) + unit tests. Playwright config + the three required scenarios are
written against the seeded users/data but **require the live stack** (`make up` + `make seed`
+ Keycloak), which isn't runnable in this sandbox (no `mkcert`, ports 80/443 bound) — so they
are marked `[~]`. Clean-checkout startup is documented in the README; full `make up` needs
`mkcert` installed locally.
