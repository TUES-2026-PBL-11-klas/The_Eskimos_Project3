"""Application configuration via pydantic-settings.

All runtime configuration is read from environment variables / a local `.env`. No secret
literals live in code (gitleaks enforces this); `TICKETMASTER_API_KEY` is read here only.
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

    database_url: str = "postgresql+asyncpg://eventhub:eventhub@localhost:5432/eventhub"
    log_level: str = "INFO"

    # --- Public API sources ---
    # app_id is a self-assigned identifier string (no OAuth, no secret).
    bandsintown_app_id: str = "eventhub-school-project"
    # Curated artist list the Bandsintown source iterates over (CSV in env).
    # NoDecode stops pydantic-settings from trying to JSON-decode the env value so the
    # validator below can split it on commas.
    bandsintown_artists: Annotated[list[str], NoDecode] = []
    # Free Ticketmaster Discovery key; None disables that source. Never hard-coded.
    ticketmaster_api_key: str | None = None

    # --- Scraper runtime ---
    scrape_max_concurrency: int = 5
    http_timeout_seconds: int = 15
    # Sources to run this pass (CSV in env). Empty = every registered scraper.
    enabled_sources: Annotated[list[str], NoDecode] = []

    # --- Retention / cleanup worker (Phase 8) ---
    cleanup_grace_days: int = 1

    # --- Observability ---
    # Prometheus Pushgateway URL (e.g. http://pushgateway:9091). Empty/None = skip the push;
    # ingestion is a one-shot job, so it pushes its run metrics here instead of being scraped.
    pushgateway_url: str | None = None

    @field_validator("bandsintown_artists", "enabled_sources", mode="before")
    @classmethod
    def _split_csv(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


settings = Settings()
