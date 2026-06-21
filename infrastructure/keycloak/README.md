# Keycloak realm import (added in Phase 2)

This directory is mounted into Keycloak at `/opt/keycloak/data/import` and loaded
via `start-dev --import-realm`.

Phase 0 intentionally ships **no realm file** — authentication is Phase 2's
deliverable. In Phase 2 add `nextup-realm.json` containing:

- **Realm:** `nextup`
- **Roles:** `player`, `organizer`, `admin`
- **Clients:**
  - `nextup-web` — public client, Authorization Code + PKCE, redirect URIs for
    `https://nextup.local/*` (no client secret in the browser).
  - `nextup-api` — audience/resource the backend validates the access token against.
- **Test users** (spec §19, dev-only credentials documented in the README):
  one admin, one organizer, three players.

`KC_HOSTNAME=auth.nextup.local` ensures the token issuer matches for both the
browser and the FastAPI backend (which validates JWTs against the realm JWKS).
