#!/usr/bin/env bash
# Run the backend test suite against a throwaway PostgreSQL container.
# The schema uses Postgres-specific features (timestamptz, partial unique
# indexes, FOR UPDATE, jsonb), so tests require a real Postgres — not SQLite.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_DIR="$(dirname "$SCRIPT_DIR")/apps/api"

CONTAINER="${NEXTUP_TEST_PG_CONTAINER:-nextup-test-pg}"
PORT="${NEXTUP_TEST_PG_PORT:-55432}"

# If TEST_DATABASE_URL is already provided (e.g. in CI), use it directly.
if [[ -z "${TEST_DATABASE_URL:-}" ]]; then
  docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
  docker run -d --name "$CONTAINER" \
    -e POSTGRES_PASSWORD=test -e POSTGRES_DB=nextup_test \
    -p "${PORT}:5432" postgres:16 >/dev/null
  trap 'docker rm -f "$CONTAINER" >/dev/null 2>&1 || true' EXIT
  for _ in $(seq 1 30); do
    docker exec "$CONTAINER" pg_isready -U postgres >/dev/null 2>&1 && break
    sleep 1
  done
  export TEST_DATABASE_URL="postgresql+asyncpg://postgres:test@localhost:${PORT}/nextup_test"
fi

cd "$API_DIR"
uv run pytest "$@"
