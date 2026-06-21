# Security

Threat model and control mapping for NextUp. Controls are implemented progressively
(auth in Phase 2, hardening in Phase 8) and documented here as they land.

## Trust boundaries

- **Browser ↔ everything:** untrusted. The frontend is a public OIDC client; the backend
  never trusts role or ownership claims it sends.
- **Keycloak:** the identity authority. Owns credentials; issues signed JWTs.
- **FastAPI backend:** the security decision point and source of truth. Validates tokens,
  authorizes every action, owns the database.
- **Internal Docker network:** Postgres/Redis/Mailpit are not exposed publicly; only Caddy
  publishes ports 80/443.

## Primary threats & controls

| Threat | Control |
| --- | --- |
| Forged / tampered tokens | Validate JWT signature against realm JWKS; check `iss`, `aud`, `exp`. Issuer matches browser+backend via shared `auth.nextup.local` host. |
| Privilege escalation via frontend claims | Backend enforces RBAC from **token roles only**; frontend role checks are UX-only. |
| Acting on others' resources (IDOR) | Object-level authorization: organizers may modify only gyms/runs they own; players only their own registrations; admin overrides. Checked in services, not handlers alone. |
| Two players claim the final slot | Registration/promotion run in one transaction with `SELECT … FOR UPDATE` row locks; lost races return `409`. |
| Injection | SQLAlchemy parameterized queries; Pydantic/Zod input validation; no string-built SQL. |
| Abuse of sensitive endpoints | Rate limiting on registration/auth-adjacent endpoints (Phase 8). |
| Secret leakage | No secrets in source; `.env` gitignored; `.env.example` uses `CHANGE_ME_` placeholders; CI scans. |
| Sensitive data in logs | Structured logs redact tokens, passwords, full `Authorization` headers, and PII. |
| Information leak via errors | Safe, generic error messages to clients; details stay server-side. |
| Cross-origin abuse | CORS restricted to the configured web origin(s). |
| Common web attacks | Secure HTTP headers (HSTS, X-Content-Type-Options, frame options, referrer policy) via the app/proxy. |
| Vulnerable dependencies / images | Dependency and container scanning in CI (Phase 8). |
| Container compromise blast radius | Run containers as non-root where practical; least-privilege mounts (read-only config). |

## Authorization rules (summary)

- **player:** view published runs; register/cancel **own** registration; check in **self**;
  read/update **own** profile and notifications.
- **organizer:** all player abilities **plus** create/manage **own** gyms, courts, and runs;
  manage rosters/attendance for **own** runs.
- **admin:** view all users/gyms/runs; disable records; assign/revoke organizer access;
  override ownership.

## Audit logging

Organizer and admin actions (publish/cancel run, check-in, no-show, promotion, gym/role
changes) write append-only `AuditEvent` rows (actor, event type, entity, redacted metadata).

## Secrets handling

Configuration is environment-based. Real `.env` files are never committed. Development
credentials are clearly labeled dev-only (README + RUNBOOK) and must never be reused in any
real environment.
