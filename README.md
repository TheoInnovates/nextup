# NextUp 🏀

Scheduling for pickup basketball runs. NextUp does more than collect names — it tells
each player whether they're **confirmed or waitlisted**, **when to arrive**, **when
they're expected to play**, and **their position in the queue**, and promotes the next
player automatically when someone cancels.

> **Core promise:** players should know when to arrive and when they'll play instead of
> waiting at a gym without knowing when they'll get on the court.

## The MVP workflow

1. An organizer creates a gym and schedules a run (capacity, courts, players/team, timing).
2. A player signs up, views the run, and registers.
3. The system assigns a **confirmed slot** (with arrival + estimated play time) or a
   **waitlist position**.
4. The organizer sees the player on the roster; either party can check the player in.
5. If a confirmed player cancels, the first eligible waitlisted player is promoted and
   **notified in-app**.
6. The organizer completes the run.

## Tech stack

Next.js + TypeScript frontend · FastAPI + PostgreSQL backend · Keycloak (OIDC) auth ·
Redis + Celery for async · Caddy reverse proxy · Prometheus + Grafana · Mailpit for email.
All orchestrated with Docker Compose. See `docs/ARCHITECTURE.md`.

## Prerequisites

- Docker + Docker Compose
- [mkcert](https://github.com/FiloSottile/mkcert) (local TLS certificates)
- `make`

## Quickstart

```bash
git clone https://gitlab.devhub.ninja/theo/project-6-nextup.git
cd project-6-nextup
make setup     # copies .env.example -> .env, generates *.local TLS certs (needs mkcert)
# add the hostnames printed by setup to /etc/hosts (all -> 127.0.0.1)
make up        # starts the stack
make migrate   # apply database migrations
make seed      # load demo data (gym, runs, dev users' profiles)
```

Then sign in at https://nextup.local with a dev user (see `docs/RUNBOOK.md`), e.g.
`organizer1` / `organizer1pass` or `player1` / `player1pass`.

> **Phase status:** the MVP (**Phases 1–9**) is implemented — auth, gyms/courts, runs,
> registration + scheduling, waitlist promotion + notifications, roster/check-in,
> observability, seed + E2E. See `docs/TASKS.md` for per-item status and
> `docs/RELEASE_NOTES.md` for what's included and known limitations.

### Local URLs (once services are running)

| Service     | URL                              |
| ----------- | -------------------------------- |
| Web app     | https://nextup.local             |
| API         | https://api.nextup.local/api/v1  |
| Keycloak    | https://auth.nextup.local        |
| Mailpit     | https://mail.nextup.local        |
| Grafana     | https://grafana.nextup.local     |
| Prometheus  | https://prometheus.nextup.local  |

### Development-only credentials

> ⚠️ Development only — never reuse these anywhere real. Defined in `.env.example`
> (placeholders) and in the Keycloak realm import (added in Phase 2). Seed users and
> their passwords are documented in `docs/RUNBOOK.md` once seeding lands (Phase 9).

## Make commands

| Command          | Purpose                                          |
| ---------------- | ------------------------------------------------ |
| `make setup`     | Bootstrap `.env` + mkcert TLS certs              |
| `make up` / `down` / `restart` | Manage the stack                   |
| `make logs s=api`| Tail one service's logs                          |
| `make migrate`   | Run Alembic migrations (Phase 1+)                |
| `make seed`      | Load dev seed data (Phase 9)                     |
| `make test`      | Backend + frontend tests                         |
| `make lint` / `format` | Lint / format both apps                    |
| `make validate`  | Validate the compose file                        |
| `make clean`     | Stop and remove volumes (**destructive**)        |

## Documentation

`docs/ARCHITECTURE.md` · `docs/IMPLEMENTATION_PLAN.md` · `docs/TASKS.md` ·
`docs/DATA_MODEL.md` · `docs/API.md` · `docs/SECURITY.md` · `docs/RUNBOOK.md` ·
`docs/RELEASE_NOTES.md`

## License

Internal project — not licensed for redistribution.
