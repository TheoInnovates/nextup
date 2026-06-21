"""Pytest fixtures: real-Postgres test DB with per-test transaction isolation,
plus a self-issued RS256 JWT strategy so auth/authz is testable without Keycloak.

DB strategy (Phase 1):
* A **session-scoped engine** points at ``TEST_DATABASE_URL`` (a real Postgres —
  the schema uses Postgres-specific features). The schema is created once from
  ``Base.metadata``; migration *consistency* is verified by CI's
  ``migration-validate`` (``alembic upgrade head`` / ``downgrade base``).
* **``db_session``** binds a session to one connection inside an outer
  transaction with ``join_transaction_mode="create_savepoint"`` so service-level
  ``commit()`` calls become savepoints and the whole test rolls back at teardown.
* **``client``** overrides ``get_db`` (shared transaction) and
  ``get_token_verifier`` (test public key) — the same ``verify()`` code path runs.

Auth strategy (Phase 2): tests mint RS256 tokens with a throwaway keypair; the
verifier is given the matching public key. Concurrency tests bypass the rollback
fixture (they need genuinely concurrent transactions).
"""

from __future__ import annotations

import os
import time
from collections.abc import AsyncGenerator, Callable

import jwt
import pytest
import pytest_asyncio
from app.core.ratelimit import registration_rate_limit
from app.core.security import TokenVerifier, get_token_verifier
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")

TEST_ISSUER = "https://auth.test.local/realms/nextup"
TEST_AUDIENCE = "nextup-api"


# --- database ----------------------------------------------------------------
@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def engine() -> AsyncGenerator[AsyncEngine, None]:
    if not TEST_DATABASE_URL:
        pytest.skip("TEST_DATABASE_URL is not set (a real Postgres is required).")
    eng = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def db_session(engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    connection = await engine.connect()
    transaction = await connection.begin()
    session = AsyncSession(
        bind=connection,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    try:
        yield session
    finally:
        await session.close()
        if transaction.is_active:
            await transaction.rollback()
        await connection.close()


# --- auth keys / tokens ------------------------------------------------------
@pytest.fixture(scope="session")
def signing_key() -> tuple[str, str]:
    """A throwaway RSA keypair (private PEM for signing, public PEM for verify)."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    public_pem = (
        key.public_key()
        .public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode()
    )
    return private_pem, public_pem


@pytest.fixture
def make_token(signing_key: tuple[str, str]) -> Callable[..., str]:
    private_pem, _ = signing_key

    def _make(
        *,
        sub: str = "kc-sub-001",
        email: str | None = "player@example.com",
        roles: list[str] | None = None,
        name: str | None = None,
        preferred_username: str | None = None,
        audience: str = TEST_AUDIENCE,
        issuer: str = TEST_ISSUER,
        expires_in: int = 3600,
        extra: dict | None = None,
    ) -> str:
        now = int(time.time())
        payload: dict = {
            "sub": sub,
            "iss": issuer,
            "aud": audience,
            "iat": now,
            "exp": now + expires_in,
        }
        if email is not None:
            payload["email"] = email
        if name is not None:
            payload["name"] = name
        if preferred_username is not None:
            payload["preferred_username"] = preferred_username
        if roles is not None:
            payload["realm_access"] = {"roles": roles}
        if extra:
            payload.update(extra)
        return jwt.encode(payload, private_pem, algorithm="RS256")

    return _make


@pytest.fixture
def auth_headers(make_token: Callable[..., str]) -> Callable[..., dict[str, str]]:
    def _headers(
        *,
        roles: tuple[str, ...] = ("player",),
        sub: str = "kc-sub-001",
        email: str | None = None,
        **kwargs: object,
    ) -> dict[str, str]:
        # Distinct subjects get distinct emails (the email column is unique).
        token = make_token(
            roles=list(roles), sub=sub, email=email or f"{sub}@example.com", **kwargs
        )
        return {"Authorization": f"Bearer {token}"}

    return _headers


# --- HTTP client -------------------------------------------------------------
@pytest_asyncio.fixture
async def client(
    db_session: AsyncSession, signing_key: tuple[str, str]
) -> AsyncGenerator[AsyncClient, None]:
    _, public_pem = signing_key
    app = create_app(enable_metrics=False)
    test_verifier = TokenVerifier(issuer=TEST_ISSUER, audience=TEST_AUDIENCE, public_key=public_pem)

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_token_verifier] = lambda: test_verifier
    # Disable the Redis fixed-window limiter in tests (state would leak across cases).
    app.dependency_overrides[registration_rate_limit] = lambda: None

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
    app.dependency_overrides.clear()
