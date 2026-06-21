"""JWT validation against the Keycloak realm (signature, iss, aud, exp).

The verifier is exposed as a FastAPI dependency provider (:func:`get_token_verifier`)
so tests can override the *key source* — minting RS256 tokens with a test key —
while the exact same :meth:`TokenVerifier.verify` code path runs in tests and in
production. Keys are fetched from ``JWKS_URL`` (internal Keycloak URL) while the
``iss`` claim is matched against ``OIDC_ISSUER`` (the public host) — the two are
deliberately distinct (see docs/SECURITY.md).
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

import jwt
from jwt import PyJWKClient

from app.core.config import get_settings
from app.core.exceptions import AuthenticationError
from app.enums import UserRole
from app.schemas.user import TokenClaims

_APP_ROLES = {role.value for role in UserRole}
_ALGORITHMS = ["RS256"]
_LEEWAY_SECONDS = 10


def _extract_roles(payload: dict) -> list[str]:
    """Return the app roles present in the token's realm_access.roles."""
    realm_access = payload.get("realm_access") or {}
    roles = realm_access.get("roles") or []
    return [role for role in roles if role in _APP_ROLES]


class TokenVerifier:
    """Validates a bearer token and returns :class:`TokenClaims`.

    Exactly one key source is used: a live JWKS endpoint (production) or a static
    public key (tests).
    """

    def __init__(
        self,
        *,
        issuer: str,
        audience: str,
        jwks_url: str | None = None,
        public_key: str | None = None,
        algorithms: list[str] | None = None,
    ) -> None:
        if not jwks_url and not public_key:
            raise ValueError("TokenVerifier needs either jwks_url or public_key")
        self.issuer = issuer
        self.audience = audience
        self.algorithms = algorithms or _ALGORITHMS
        self._public_key = public_key
        self._jwk_client = PyJWKClient(jwks_url) if jwks_url and not public_key else None

    def _signing_key(self, token: str) -> Any:
        if self._jwk_client is not None:
            return self._jwk_client.get_signing_key_from_jwt(token).key
        return self._public_key

    def verify(self, token: str) -> TokenClaims:
        try:
            signing_key = self._signing_key(token)
            payload = jwt.decode(
                token,
                signing_key,
                algorithms=self.algorithms,
                audience=self.audience,
                issuer=self.issuer,
                leeway=_LEEWAY_SECONDS,
                options={"require": ["exp", "iat", "sub"]},
            )
        except jwt.PyJWTError as exc:
            # Do not leak the specific reason to the client.
            raise AuthenticationError("Invalid or expired authentication token.") from exc

        return TokenClaims(
            sub=payload["sub"],
            email=payload.get("email"),
            preferred_username=payload.get("preferred_username"),
            name=payload.get("name"),
            roles=_extract_roles(payload),
        )


@lru_cache
def get_token_verifier() -> TokenVerifier:
    """FastAPI dependency provider for the production verifier (JWKS-backed)."""
    settings = get_settings()
    return TokenVerifier(
        issuer=settings.oidc_issuer,
        audience=settings.oidc_audience,
        jwks_url=settings.jwks_url,
    )
