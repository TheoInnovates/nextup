"""JWT verification tests (signature, iss, aud, exp, role extraction)."""

from __future__ import annotations

from collections.abc import Callable

import jwt
import pytest
from app.core.exceptions import AuthenticationError
from app.core.security import TokenVerifier
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from tests.conftest import TEST_AUDIENCE, TEST_ISSUER


@pytest.fixture
def verifier(signing_key: tuple[str, str]) -> TokenVerifier:
    _, public_pem = signing_key
    return TokenVerifier(issuer=TEST_ISSUER, audience=TEST_AUDIENCE, public_key=public_pem)


def test_valid_token_yields_claims(verifier: TokenVerifier, make_token: Callable[..., str]) -> None:
    token = make_token(sub="abc", email="a@b.com", name="Ann", roles=["player", "organizer"])
    claims = verifier.verify(token)
    assert claims.sub == "abc"
    assert claims.email == "a@b.com"
    assert claims.name == "Ann"
    assert set(claims.roles) == {"player", "organizer"}


def test_roles_filtered_to_app_roles(
    verifier: TokenVerifier, make_token: Callable[..., str]
) -> None:
    token = make_token(roles=["player", "offline_access", "uma_authorization"])
    claims = verifier.verify(token)
    assert claims.roles == ["player"]


def test_expired_token_rejected(verifier: TokenVerifier, make_token: Callable[..., str]) -> None:
    token = make_token(expires_in=-10)
    with pytest.raises(AuthenticationError):
        verifier.verify(token)


def test_wrong_audience_rejected(verifier: TokenVerifier, make_token: Callable[..., str]) -> None:
    token = make_token(audience="some-other-client")
    with pytest.raises(AuthenticationError):
        verifier.verify(token)


def test_wrong_issuer_rejected(verifier: TokenVerifier, make_token: Callable[..., str]) -> None:
    token = make_token(issuer="https://evil.example/realms/nextup")
    with pytest.raises(AuthenticationError):
        verifier.verify(token)


def test_bad_signature_rejected(verifier: TokenVerifier) -> None:
    # Sign with a *different* key than the verifier trusts.
    other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    other_pem = other.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    forged = jwt.encode(
        {"sub": "x", "iss": TEST_ISSUER, "aud": TEST_AUDIENCE, "iat": 0, "exp": 9_999_999_999},
        other_pem,
        algorithm="RS256",
    )
    with pytest.raises(AuthenticationError):
        verifier.verify(forged)
