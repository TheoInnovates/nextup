# Implementation Plan

NextUp is built incrementally across ten phases. **The application stays deployable after
every phase.** Each phase delivers the smallest functional vertical slice, tests it, and
keeps documentation in sync (spec §22). A task is "done" only per the Definition of Done
(spec §20) — not on code generation alone.

## Working process

- **Before a phase:** review `docs/TASKS.md`, inspect relevant code, state the change, list
  affected files + migrations + tests, update the checklist.
- **During:** implement the smallest slice → run its tests → fix failures before moving on →
  keep docs synced → avoid unrelated refactoring → preserve backward compatibility unless a
  migration is documented.
- **After:** summarize what was built, files added/changed, migrations, tests + results,
  security considerations, known limitations, and the next recommended task.

## Phases

### Phase 0 — Repository & documentation ✅ (this deliverable)
Repo structure, `CLAUDE.md`, `README.md`, all `docs/`, `.env.example`, `Makefile`, starter
`docker-compose.yml`, Caddy base config, CI skeleton.
**Exit:** docs internally consistent; service responsibilities defined; local-env structure
established; `docker compose config` validates. No app features.

### Phase 1 — Infrastructure & service scaffolding
Next.js + FastAPI scaffolds; Postgres + Redis connections; Alembic; Keycloak + Caddy wired;
`/health` + `/ready` endpoints; structured JSON logging; basic CI.
**Exit:** whole stack starts with `make up`; web calls the API health endpoint; backend
connects to Postgres + Redis; auth config loads; CI passes.
**First slice:** FastAPI `GET /api/v1/health` + `GET /api/v1/ready` (ready checks Postgres +
Redis) behind Caddy at `api.nextup.local`, with JSON logging and a CI job that runs it.

### Phase 2 — Authentication & users
Keycloak realm import (roles, clients, test users); frontend login; backend token validation;
`/me` (GET/PATCH); user-profile sync from claims; role-protected routes.
**Exit:** player/organizer/admin can sign in; unauthorized requests rejected correctly;
backend enforces roles independently; auth tests pass.

### Phase 3 — Gym & court management
Gym + Court models + migrations; gym/court APIs with ownership controls; organizer gym pages.
**Exit:** organizer creates/manages a gym; cannot modify another's gym; admin sees all; tests pass.

### Phase 4 — Basketball-run management
Run model + status machine; create/edit forms; publish/cancel actions; upcoming-run list;
run-details page; timezone handling.
**Exit:** organizer creates+publishes a run; players see published runs; drafts hidden;
invalid transitions rejected; tests pass.

### Phase 5 — Registration & scheduling engine
Registration model; deterministic scheduling service; capacity controls; confirmed/waitlisted
assignment; arrival + play-time calculation; duplicate-registration protection; player
registration page.
**Exit:** registration is transactionally safe; correct confirmed/waitlist assignment; players
see their timing; concurrent final-slot registration is tested; tests pass.

### Phase 6 — Cancellation & waitlist promotion
Player + organizer cancellation; automatic promotion; queue recalculation; in-app
notification; audit events.
**Exit:** cancelling a confirmed player promotes the correct waitlisted player atomically;
queue positions accurate; promoted player notified; tests pass.

### Phase 7 — Roster & check-in
Organizer roster + waitlist view; check-in; no-show; run start/complete controls;
mobile-friendly check-in screen.
**Exit:** organizer manages attendance; players see updated status; unauthorized users can't
modify attendance; tests pass.

### Phase 8 — Observability & production hardening
Prometheus metrics; Grafana dashboard; improved logging; rate limits; security headers; error
handling; dependency + container scans; `docs/RUNBOOK.md`.
**Exit:** health/readiness work; metrics visible; logs carry request correlation; security
scans run in CI; runbook covers common ops.

### Phase 9 — End-to-end validation
Seeded demo environment; Playwright tests (3 required scenarios); final README; API docs;
demo instructions; known limitations; release notes.
**Exit:** all three E2E scenarios pass; the app starts from a clean checkout; a new developer
can follow the README; the MVP workflow works without manual DB changes.

## Open questions / assumptions

- Production deployment target is undecided; CI `deploy` stays manual until chosen.
- Default scheduling assumptions (game length, arrival lead) are per-run configurable; the
  Phase 5 formula may be refined but must stay deterministic and tested.
