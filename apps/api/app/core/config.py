"""Application configuration loaded from environment variables.

All settings come from the environment (12-factor). `.env` is read for local
development only; in containers the values are injected via `env_file`.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application settings.

    Field names map to upper-cased environment variables (case-insensitive), so
    ``database_url`` is read from ``DATABASE_URL``.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Runtime ---------------------------------------------------------------
    app_env: str = "local"
    log_level: str = "INFO"

    # --- Datastores ------------------------------------------------------------
    # SQLAlchemy async DSN (asyncpg driver). Alembic reuses this value.
    database_url: str = "postgresql+asyncpg://nextup:nextup@postgres:5432/nextup"
    redis_url: str = "redis://redis:6379/0"

    # --- OIDC / auth (validated by the backend in Phase 2) ---------------------
    oidc_issuer: str = "https://auth.nextup.local/realms/nextup"
    oidc_audience: str = "nextup-api"
    jwks_url: str = "https://auth.nextup.local/realms/nextup/protocol/openid-connect/certs"

    # --- HTTP ------------------------------------------------------------------
    cors_origins: list[str] = ["https://nextup.local"]

    # --- Celery ----------------------------------------------------------------
    celery_broker_url: str = "redis://redis:6379/1"
    celery_result_backend: str = "redis://redis:6379/2"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_csv(cls, value: object) -> object:
        """Allow CORS origins to be supplied as a comma-separated string."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def is_local(self) -> bool:
        return self.app_env.lower() in {"local", "dev", "development", "test"}


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (read once per process)."""
    return Settings()
