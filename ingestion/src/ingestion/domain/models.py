"""Source-agnostic event models.

Two deliberately separate shapes:

* ``RawEvent`` — whatever a scraper managed to pull, loosely typed (mostly optional
  strings + the original payload). Produced by scrapers, consumed by the Validator.
* ``NormalizedEvent`` — cleaned and typed, ready to persist (UTC datetimes, parsed
  prices, computed ``dedup_key``, resolved category). Produced by the Normalizer,
  consumed by the repository.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ingestion.domain.categories import Category


class RawEvent(BaseModel):
    """Loosely-typed event exactly as scraped."""

    model_config = ConfigDict(extra="ignore")

    source: str
    external_id: str | None = None
    title: str | None = None
    description: str | None = None
    # Raw, unparsed start date/time string as it appeared on the source.
    start_raw: str | None = None
    url: str | None = None
    venue_name: str | None = None
    venue_city: str | None = None
    # Source-provided category hint, used as a fallback by the Categorizer.
    category_hint: str | None = None
    # The original scraped dict, preserved for debugging / re-processing.
    raw_payload: dict[str, Any] = Field(default_factory=dict)


class NormalizedEvent(BaseModel):
    """Cleaned, typed event ready for persistence."""

    model_config = ConfigDict(extra="ignore")

    source: str
    external_id: str
    title: str
    description: str | None = None
    start_at: datetime
    url: str

    venue_name: str | None = None
    venue_city: str | None = None

    # Resolved by the Categorizer; defaults to the explicit fallback.
    category: Category = Category.UNCATEGORIZED

    # Deterministic cross-source identity (computed by the Normalizer).
    dedup_key: str
    raw_payload: dict[str, Any] = Field(default_factory=dict)
