#!/usr/bin/env bash
# NextUp local setup: bootstrap .env and generate mkcert TLS certs for *.local.
# Idempotent. Bringing services up is `make up` (Phase 1 wires the app images).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$REPO_ROOT"

CERTS_DIR="infrastructure/caddy/certs"
HOSTS=(nextup.local api.nextup.local auth.nextup.local mail.nextup.local grafana.nextup.local prometheus.nextup.local)

# 1. .env
if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env from .env.example — review CHANGE_ME_* values."
else
  echo ".env already exists — leaving it untouched."
fi

# 2. TLS certs via mkcert
mkdir -p "$CERTS_DIR"
if [[ -f "$CERTS_DIR/cert.pem" && -f "$CERTS_DIR/key.pem" ]]; then
  echo "TLS certs already present in $CERTS_DIR."
elif command -v mkcert >/dev/null 2>&1; then
  mkcert -install
  mkcert -cert-file "$CERTS_DIR/cert.pem" -key-file "$CERTS_DIR/key.pem" "${HOSTS[@]}"
  echo "Generated TLS certs in $CERTS_DIR."
else
  echo "WARNING: mkcert not found. Install it (https://github.com/FiloSottile/mkcert)"
  echo "         then re-run 'make setup' to generate certs for ${HOSTS[*]}."
fi

# 3. /etc/hosts reminder
echo
echo "Ensure these hostnames resolve to 127.0.0.1 (add to /etc/hosts):"
printf '  127.0.0.1 %s\n' "${HOSTS[@]}"
echo
echo "Setup complete. Note: 'make up' starts services beginning in Phase 1."
