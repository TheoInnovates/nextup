import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright configuration for NextUp's end-to-end suite (spec §19 / Phase 9).
 *
 * These tests exercise the REAL stack through the browser: web → Caddy →
 * FastAPI → Postgres/Redis, with Keycloak handling login. They are NOT part of
 * the unit-test (vitest) job and require the stack to be running first:
 *
 *   make up && make seed
 *
 * They are driven against the seeded demo data, so they assume a fresh
 * `make seed` (some scenarios mutate shared registration state). Run them
 * serially (see `workers`/`fullyParallel` below) for that reason.
 *
 * The stack is started out-of-band via `make up`, so there is deliberately no
 * `webServer` block here — Playwright connects to an already-running app.
 */
export default defineConfig({
  testDir: "./e2e",
  // mkcert TLS certs aren't in the browser trust store; accept them.
  // Shared seeded state means scenarios can't safely run in parallel.
  fullyParallel: false,
  workers: 1,
  // Locally we want deterministic, non-flaky runs; no retries.
  retries: 0,
  // A generous per-test budget: each scenario does a full Keycloak login.
  timeout: 60_000,
  expect: { timeout: 10_000 },
  reporter: [["list"]],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "https://nextup.local",
    ignoreHTTPSErrors: true,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
