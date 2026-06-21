# NextUp — Phase 0: Repository & Documentation

## Context

NextUp is a basketball-run scheduling platform (production-minded MVP). The core promise:
players should know **when to arrive** and **when they'll play** instead of waiting at a gym
blindly. The build is staged into Phases 0–9; **this task delivers only Phase 0** — repository
structure, documentation, and infrastructure scaffolding config. **No application code, no
running services.** Exit criteria: docs are internally consistent, service responsibilities are
defined, and the local-environment structure exists. Phases 1–9 are scoped in the plan docs but
not implemented now.

The repo will be its own git repository pushed to `gitlab.devhub.ninja`, living at
`/home/tforrester/projects/project-6-nextup/` (matching the user's `project-N-name` convention;
the repo's internal root follows the spec's `nextup/` layout).

### Locked decisions (from user)
- **Location:** `/home/tforrester/projects/project-6-nextup/` (own git repo).
- **Routing/TLS:** Match the existing infra convention from `project-4-workspace` —
  label-driven `caddy-docker-proxy` + mkcert `*.local` certs. Hosts:
  `nextup.local` (web), `api.nextup.local` (api), `auth.nextup.local` (Keycloak),
  `mail.nextup.local` (Mailpit), `grafana.nextup.local`, `prometheus.nextup.local`.
- **Auth:** Next.js as a **public OIDC client using Authorization Code + PKCE**; FastAPI
  validates JWTs independently (JWKS from Keycloak). Because both browser and backend reach
  Keycloak through the same `auth.nextup.local` host via Caddy, the token **issuer matches** on
  both sides (set `KC_HOSTNAME=auth.nextup.local`) — avoids the classic OIDC issuer-mismatch bug.

### Reference patterns to reuse (from `project-4-workspace`)
- `docker-compose.yml` service template: pinned image, `container_name`, `restart: unless-stopped`,
  `networks: [nextup]`, healthcheck on every service, `deploy.resources.limits.memory`,
  `depends_on: { condition: service_healthy }`, `caddy.*` labels for routing.
- `caddy/Caddyfile`: minimal global block + `(tls_certs)` snippet; per-service routing via labels.
- `prometheus/prometheus.yml`, `grafana/provisioning/{datasources,dashboards}`.
- `Makefile` delegating to `scripts/*.sh`; `.env.example` with `CHANGE_ME_` placeholders,
  real `.env*` gitignored.
- CI: spec mandates **GitLab CI** (`.gitlab-ci.yml`), not the GitHub Actions used in infra repos.

---

## Deliverables (Phase 0)

Create the repo at `/home/tforrester/projects/project-6-nextup/`.

### 1. Directory skeleton (with `.gitkeep` in otherwise-empty dirs)
Per spec §7:
```
apps/web/{app,components,features,hooks,lib,tests}
apps/api/app/{api,core,db,models,schemas,services,repositories,scheduling,workers}
apps/api/{tests,alembic}
infrastructure/{caddy,keycloak,prometheus,grafana,docker}
docs/
scripts/
```
No `package.json`/`pyproject.toml` content beyond minimal placeholders is required in Phase 0;
real scaffolding happens in Phase 1. Keep Phase-0 files limited to docs + infra config so the
repo stays deployable-by-design but feature-free.

### 2. Root files
- **`CLAUDE.md`** — project overview, tech stack, repo map, per-phase status, common commands,
  conventions (UTC storage / gym-timezone display, backend-is-source-of-truth, thin route
  handlers → services → repositories), local credentials pointer. Follow the concise/runnable
  tone of `project-4-workspace/CLAUDE.md`.
- **`README.md`** — what NextUp is, the core promise, the MVP workflow (spec §3), prerequisites
  (Docker, mkcert), quickstart (`make setup && make up`), service URLs (`*.local` hosts),
  documented **dev-only** credentials, Makefile command reference, current phase status.
- **`.env.example`** — all config vars with safe placeholders, no real secrets. Sections:
  domain/hosts, Postgres, Redis, Keycloak (realm `nextup`, clients `nextup-web` public +
  `nextup-api` audience), backend (`DATABASE_URL`, `REDIS_URL`, `OIDC_ISSUER`, `OIDC_AUDIENCE`,
  `JWKS_URL`, `CORS_ORIGINS`, `LOG_LEVEL`), web (`NEXT_PUBLIC_API_URL`, OIDC client id/issuer),
  Celery, Mailpit, Grafana admin (`CHANGE_ME_*`). Document UTC default.
- **`Makefile`** — `setup, up, down, restart, logs, migrate, seed, test, test-api, test-web,
  lint, format, clean` (all spec §16). Phase-0 targets may print "implemented in Phase N" where
  a service doesn't exist yet, but `up/down/logs/clean` work against the compose file now.
- **`docker-compose.yml`** — *starter* file (spec §23 says "starter `docker-compose.yml`"). All
  spec §16 services are **declared** (`web, api, postgres, redis, celery-worker, keycloak,
  mailpit, caddy, prometheus, grafana`) with the `nextup` network, named volumes, restart
  policies, healthcheck/`depends_on` shape, and Caddy labels — structured so
  `docker compose config --quiet` **validates**. Phase 0 does **not** require any service to
  actually start (that's Phase 1's exit criterion); `web/api/celery-worker` reference build
  contexts under `apps/*` that don't exist yet, which is fine for config validation. Document
  that bringing services up is Phase 1 work.
- **`.gitignore`** — `.env`, `.env.*` (keep `.env.example`), `node_modules`, `__pycache__`,
  `.venv`, `infrastructure/caddy/certs/`, volume dirs, build artifacts.
- **`.gitlab-ci.yml`** — *skeleton only.* Stages `validate, lint, test, build, security-scan,
  package, deploy` (spec §17) with the single **`validate` job that actually runs**
  (`docker compose config --quiet`). The lint/typecheck/test/build/scan/package jobs are
  declared as documented stubs to be filled in **with their apps in later phases** (the spec
  assigns "Basic CI pipeline" to Phase 1). Manual `deploy` placeholder.

### 3. `docs/`
- **`ARCHITECTURE.md`** — logical architecture diagram (spec §6), component responsibilities,
  request/auth flow (browser → Caddy → web/api; OIDC PKCE → Keycloak → JWT → FastAPI JWKS
  validation), modular-monolith rationale, layering (api/services/repositories/scheduling),
  transaction & concurrency strategy for final-slot/promotion (row locks via
  `SELECT … FOR UPDATE` on run capacity), UTC-storage/timezone-display rule, key ADR-style
  decisions (Keycloak public+PKCE, label-driven Caddy, Celery for async).
- **`IMPLEMENTATION_PLAN.md`** — Phases 0–9 restated with deliverables, exit criteria, and the
  recommended first vertical slice per phase; the working process (smallest vertical slice →
  test → keep deployable). Marks Phase 0 in progress, 1–9 pending.
- **`TASKS.md`** — checklist for all phases using the required markers
  (`[ ]` not started, `[~]` in progress, `[x]` done, `[!]` blocked). Phase 0 items map 1:1 to
  these deliverables.
- **`DATA_MODEL.md`** — full ERD description: `UserProfile, Gym, Court, BasketballRun,
  RunRegistration, Notification, AuditEvent` (spec §8) with fields, types, UUID PKs, FKs,
  enums (run status, registration status), and constraints (one active registration per
  player/run via partial unique index, deterministic queue positions, audit-preserving cancels).
  Document the scheduling formula (spec §9) and its invariants.
- **`API.md`** — all `/api/v1` endpoints (spec §10) with methods, auth/role requirements,
  request/response sketch, status codes, pagination/error-envelope conventions. Marked as the
  contract; implemented in later phases.
- **`SECURITY.md`** — threat model + control mapping (spec §13): OIDC/JWT validation, RBAC +
  object-level ownership rules (organizer owns gyms/runs; player owns registrations; admin
  override), input validation, security headers, CORS, rate limiting on sensitive endpoints,
  no committed secrets, audit logging, non-root containers, dependency/container scanning,
  log redaction, safe errors.
- **`RUNBOOK.md`** — operational basics: start/stop, mkcert setup, migrations, seed, logs,
  health/readiness checks, resetting local data, common failure modes. (Fleshed out in Phase 8;
  Phase 0 establishes the skeleton.)

### 4. `infrastructure/` config (Phase-0 skeletons only)
Phase 0 establishes the directory layout and the Caddy base config; the realm import, scrape
configs, and dashboards are **deferred to the phases that own them** (Keycloak realm + test users
= Phase 2; real Prometheus/Grafana = Phase 8). This keeps Phase 0 to structure + the review gate.
- `caddy/Caddyfile` — global block + `(tls_certs)` snippet (label-driven proxy handles routes).
  This is static config that doesn't depend on app code, so it's reasonable to write now; a
  `certs/` dir with `.gitkeep` (real certs gitignored, generated later).
- `keycloak/` — `.gitkeep` + a short README noting the `nextup` realm, roles
  `player/organizer/admin`, clients `nextup-web` (public, PKCE) / `nextup-api` (audience), and
  test users will be added as the realm import in **Phase 2**. At most a minimal realm/roles
  stub; **no test users or login verification in Phase 0.**
- `prometheus/` — `.gitkeep` + note; real `prometheus.yml` scrape config in **Phase 8**.
- `grafana/` — `.gitkeep` + note; provisioned datasource/dashboards in **Phase 8**.
- `docker/` — `.gitkeep` + note for Dockerfiles added in Phase 1.

### 5. `scripts/`
- `.gitkeep` + a short note. `setup.sh` (mkcert certs, `.env` bootstrap), `seed`, and `migrate`
  scripts are documented as Phase 1+/5 work; `make setup` may exist as a documented stub now.
  No script needs to successfully run against live services in Phase 0.

---

## Out of scope for Phase 0 (explicitly deferred)
- Any FastAPI/Next.js source, models, migrations, or tests (Phases 1–7).
- Running `web/api/celery-worker` containers (Phase 1).
- Real Prometheus metrics / Grafana dashboards / rate limiting (Phase 8).
- Playwright/pytest/vitest test code (per-phase).

---

## Verification (Phase 0)
Phase 0 has **no application features and no running services** to test (starting services is
Phase 1's exit criterion). Verify structure, validity, and documentation consistency only:
1. `cd /home/tforrester/projects/project-6-nextup && git init`; confirm the tree matches spec §7.
2. `docker compose config --quiet` succeeds (the compose file is syntactically valid).
3. Cross-check docs for internal consistency: endpoints in `API.md` ↔ spec §10; entities/fields
   in `DATA_MODEL.md` ↔ spec §8; tasks in `TASKS.md` ↔ deliverables above; `.env.example` keys ↔
   services referenced in compose/docs.
4. No real secrets committed: `grep -ri CHANGE_ME` shows only placeholders; `.env` is gitignored.
5. Makefile targets are present (spec §16) and `make` with no service running doesn't error on
   parse; targets for not-yet-built services clearly state the phase that implements them.

## Phase 0 → Phase 1 handoff
End-of-phase summary will recommend the **first Phase 1 vertical slice**:
> FastAPI app skeleton (`apps/api/app/main.py`) exposing `GET /api/v1/health` and
> `GET /api/v1/ready` (readiness checks Postgres + Redis), wired into `docker-compose.yml` behind
> Caddy at `api.nextup.local`, with structured JSON logging and a CI job that runs it — proving
> the end-to-end path browser → Caddy → FastAPI → Postgres/Redis before any domain features.
