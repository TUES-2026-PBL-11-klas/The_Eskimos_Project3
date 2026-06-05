"""Application configuration via pydantic-settings.

All runtime configuration is read from environment variables / a local `.env`. No secret
literals live in code; database credentials and tokens are supplied only through the
environment. This service connects to two databases — see ``EVENTS_DB_URL`` (read-only,
owned by the ingestion service) and ``USERS_DB_URL`` (read-write, owned here).
"""

from __future__ import annotations

from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Databases ---
    # Events DB: read-only. Owned/written by the ingestion service. The default points at the
    # ingestion compose Postgres exposed on the host; the api container overrides the host.
    events_db_url: str = "postgresql+asyncpg://eventhub:eventhub@localhost:5432/eventhub"
    # Users DB: read-write, owned by this service. Declared now but unused until Phase 4.
    users_db_url: str = "postgresql+asyncpg://eventhub:eventhub@localhost:5433/eventhub_users"

    # --- Connection pooling (applied to both engines) ---
    db_pool_size: int = 5
    db_max_overflow: int = 10

    # --- Auth / sessions (used from Phase 6) ---
    session_token_ttl_hours: int = 720  # 30 days
    session_token_bytes: int = 32
    bcrypt_rounds: int = 12

    # --- Event reads ---
    cache_max_age_seconds: int = 300

    # --- Reminders (used from Phase 8) ---
    reminder_default_lead_hours: int = 24

    # --- HTTP ---
    log_level: str = "INFO"
    # Allowed CORS origins (CSV in env). Empty = none (restrictive by default).
    cors_origins: Annotated[list[str], NoDecode] = []

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_csv(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


settings = Settings()
