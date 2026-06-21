# Runbook

Operational tasks for NextUp. **Skeleton in Phase 0; expanded in Phase 8** as metrics,
logging, and rate limits land.

## Local environment

```bash
make setup     # .env + mkcert *.local certs (one time)
make up        # start the stack          make down     # stop
make logs s=api  # tail one service       make restart  # restart
make clean     # stop + remove volumes (DESTRUCTIVE)
```

Hostnames (add to `/etc/hosts`, all → 127.0.0.1): `nextup.local`, `api.nextup.local`,
`auth.nextup.local`, `mail.nextup.local`, `grafana.nextup.local`, `prometheus.nextup.local`.

> Phase status: application services start in Phase 1; the Keycloak realm import lands in
> Phase 2; metrics/dashboards in Phase 8; seed data in Phase 9.

## Database & migrations (Phase 1+)

```bash
make migrate                              # alembic upgrade head
docker compose exec api alembic revision --autogenerate -m "msg"
docker compose exec postgres psql -U nextup -d nextup
```

## Keycloak realm & dev users (Phase 2)

The `nextup` realm is imported on startup from `infrastructure/keycloak/nextup-realm.json`
(`start-dev --import-realm`). It defines realm roles `player`/`organizer`/`admin`, the
public SPA client `nextup-web` (Auth Code + PKCE, with an audience mapper that adds
`nextup-api` to access tokens), and the bearer-only `nextup-api` client.

> ⚠️ **Development-only credentials — never reuse anywhere real.**

| Username     | Password         | Roles               |
| ------------ | ---------------- | ------------------- |
| `player1`    | `player1pass`    | player              |
| `organizer1` | `organizer1pass` | organizer, player   |
| `admin1`     | `admin1pass`     | admin               |

The Keycloak admin console is at `https://auth.nextup.local` (admin/admin by default —
override `KEYCLOAK_ADMIN*` in `.env`). To re-import after editing the realm JSON, recreate
the Keycloak volume: `docker compose rm -sf keycloak && docker volume rm nextup_keycloak_data`.

## Seed data (Phase 9)

```bash
make seed   # admin + organizer + 3 players + gym + 2 courts + draft/published/full runs
```
Dev-only seed credentials will be documented here once seeding lands.

## Health & readiness

```bash
curl -k https://api.nextup.local/api/v1/health   # liveness
curl -k https://api.nextup.local/api/v1/ready    # readiness (Postgres + Redis)
docker compose ps                                # container health
```

## Observability (Phase 8)

- **Metrics:** the API exposes Prometheus metrics at `/metrics` (HTTP request count +
  latency histograms from the instrumentator, plus domain counters:
  `nextup_registrations_total{result}`, `nextup_promotions_total`,
  `nextup_checkins_total`, `nextup_task_failures_total{task}`). Prometheus
  (`infrastructure/prometheus/prometheus.yml`) scrapes `api:8000/metrics`; Grafana is
  provisioned with a Prometheus datasource and the **NextUp Overview** dashboard
  (`infrastructure/grafana/provisioning/`).
- **Dashboards/UI:** Prometheus at `https://prometheus.nextup.local`, Grafana at
  `https://grafana.nextup.local`.
- **Logs:** `make logs s=api` — structured JSON. Each request gets an `X-Request-ID`
  (generated if absent, echoed in the response); it's bound to every log line in the
  request via `structlog.contextvars` for correlation.

## Security hardening (Phase 8)

- **Security headers:** the API sets `X-Content-Type-Options`, `X-Frame-Options`,
  `Referrer-Policy`, `X-XSS-Protection`. HSTS is terminated at Caddy (HTTPS).
- **CORS:** restricted to `CORS_ORIGINS` (default `https://nextup.local`).
- **Rate limiting:** registration is rate-limited per user (Redis fixed window,
  `REGISTER_LIMIT`/min) → `429 {code: "rate_limited"}` when exceeded.
- **CI scans:** `api-dependency-scan` (pip-audit), `web-dependency-scan` (npm audit), and
  `container-scan` (Trivy) run in the `security-scan` stage (non-blocking / `allow_failure`).
- **Audit log:** organizer/admin and promotion actions append `AuditEvent` rows
  (actor, event type, entity, redacted ID-only metadata).

## Common issues

| Symptom | Likely cause / fix |
| --- | --- |
| Browser TLS warning | mkcert root not installed — re-run `make setup` (`mkcert -install`). |
| Host not found | Hostname missing from `/etc/hosts`. |
| OIDC issuer mismatch | `KC_HOSTNAME` must equal the host the browser uses (`auth.nextup.local`). |
| API can't reach DB | Check `postgres` health (`docker compose ps`) and `DATABASE_URL`. |
| Port 80/443 in use | Another proxy is bound; stop it or remap Caddy ports. |

## Reset local data

```bash
make clean && make setup && make up
```
