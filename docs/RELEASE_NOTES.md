# NextUp — Release Notes (MVP)

## Overview

The MVP delivers the full NextUp workflow across Phases 1–9: organizers create gyms,
courts, and runs; players register and are told whether they're **confirmed or
waitlisted**, **when to arrive**, and **when they'll play**; cancellations atomically
promote the next eligible waitlisted player and notify them; organizers run check-in.

## What's included

- **Auth:** Keycloak (OIDC, Auth Code + PKCE). Backend validates JWTs independently
  (JWKS, `iss`/`aud`/`exp`); RBAC (`player`/`organizer`/`admin`) + object-level ownership.
- **Domain:** gyms/courts (ownership-controlled), runs (status machine + lifecycle,
  UTC storage / gym-timezone display), registration with a deterministic scheduling
  engine, waitlist + atomic promotion, in-app notifications, audit log, roster + check-in.
- **Correctness:** registration and promotion run in one transaction with a run-row
  `SELECT … FOR UPDATE` lock; the final-slot race and atomic promotion are covered by
  **real concurrent-transaction tests** (the race test is self-proving — it fails if the
  lock is removed).
- **Ops:** structured JSON logs with request-ID correlation, Prometheus metrics +
  Grafana dashboard, rate limiting + security headers, CI (lint/type/test/build + scans),
  Dockerized stack behind Caddy, idempotent dev seed.

## Test coverage

- Backend: **92 tests** (unit scheduling engine, status machine, auth/JWT, RBAC, CRUD,
  ownership/IDOR, registration/waitlist, **2 real concurrency tests**, notifications,
  roster/check-in, observability, seed) — all green against a real PostgreSQL.
- Frontend: **81+ vitest tests** (API client, schemas, timezone formatting, component
  rendering with mocked fetch) + clean `next build`.
- Migrations: chain `0001→0005` applies and reverses cleanly (`migration-validate`).

## Known limitations

- **Sandbox verification ceiling:** the full stack over Caddy HTTPS + browser-OIDC login
  was not executed in the build environment (`mkcert` absent; host ports 80/443 bound).
  Every constituent piece is verified by running (tests, image builds, `/metrics`, JSON
  logs); items needing the live browser/IdP are marked `[~]` in `docs/TASKS.md`.
- **Playwright E2E** (3 scenarios) are written but require the live stack
  (`make up` + `make seed` + Keycloak) — not part of the unit-test CI job. See
  `apps/web/e2e/README.md`.
- **Time entry timezone:** organizers enter run times in their browser's local zone
  (converted to UTC); a future improvement is gym-zone-aware input.
- **No-show** is recorded for attendance and does not auto-promote (it occurs at run time).
- **Notifications** are in-app only; email (Mailpit) dispatch via Celery is scaffolded but
  not wired to notification creation in this MVP.
- **Deployment target** is undecided; the CI `deploy` stage is a manual placeholder.

## Running the demo

```bash
make setup            # .env + mkcert *.local certs (requires mkcert installed)
# add *.nextup.local hosts to /etc/hosts → 127.0.0.1
make up               # start the stack
make migrate          # apply DB migrations
make seed             # load demo data
```
Then sign in at `https://nextup.local` with a dev user (see `docs/RUNBOOK.md`, e.g.
`organizer1` / `organizer1pass`, `player1` / `player1pass`).
