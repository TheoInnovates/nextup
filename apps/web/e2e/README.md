# End-to-end tests (Playwright)

These are the three required end-to-end scenarios from the spec (§19 / Phase 9).
Unlike the unit tests (vitest), they drive a **real browser against the live
stack** — web → Caddy → FastAPI → Postgres/Redis, with **Keycloak** handling
login. They are **not** part of the unit-test CI job and cannot run without the
full stack up.

## Scenarios

| File                              | Scenario                                                                 |
| --------------------------------- | ------------------------------------------------------------------------ |
| `confirmed-registration.spec.ts`  | player1 registers for "Tuesday Night Run" and is confirmed with times.   |
| `waitlist-promotion.spec.ts`      | player1 cancels on "Sold-out Saturday"; player3 is promoted + notified.  |
| `check-in.spec.ts`                | organizer1 checks in a confirmed player on the run roster.               |

The specs run **serially** (`workers: 1`, `fullyParallel: false` in
`playwright.config.ts`) because they share mutable seeded registration state.
They assume a **fresh `make seed`** — re-seed before re-running.

## Prerequisites

1. Start the stack and seed demo data (from the repo root):

   ```bash
   make up
   make seed
   ```

2. Add the local hostnames to your hosts file (one-time), so the browser can
   resolve the Caddy-served domains:

   ```text
   # /etc/hosts
   127.0.0.1 nextup.local api.nextup.local auth.nextup.local
   ```

3. Install the Chromium browser Playwright drives (one-time; this is a separate
   step from `npm install` and is the only step that downloads a browser):

   ```bash
   cd apps/web
   npx playwright install --with-deps chromium
   ```

## Running

```bash
cd apps/web
E2E_BASE_URL=https://nextup.local npm run test:e2e
```

`E2E_BASE_URL` defaults to `https://nextup.local`, so it can be omitted when
using the default Compose hostnames. `ignoreHTTPSErrors` is enabled in the
config because the stack uses locally-trusted `mkcert` certificates that the
browser may not trust by default.

## Seeded users

Passwords follow the pattern `<username>pass`.

| Username     | Password         | Role      |
| ------------ | ---------------- | --------- |
| `player1`    | `player1pass`    | player    |
| `player2`    | `player2pass`    | player    |
| `player3`    | `player3pass`    | player    |
| `organizer1` | `organizer1pass` | organizer |
| `admin1`     | `admin1pass`     | admin     |

## Notes

- These tests are intentionally excluded from vitest: vitest only collects
  `**/*.test.{ts,tsx}`, and these are `*.spec.ts` under `e2e/`.
- There is no Playwright `webServer` configured — the stack is started via
  `make up`, and Playwright connects to the already-running app.
