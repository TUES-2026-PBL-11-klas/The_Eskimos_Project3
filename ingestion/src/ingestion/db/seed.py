"""Idempotent seed data: ~50 sample events across categories, with a few sources/venues.

Used for local development and as an integration-test fixture. Re-running is a no-op once
the events table already has rows. Run with: ``python -m ingestion.db.seed``.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

from slugify import slugify
from sqlalchemy import func, select

from ingestion.db.base import session_scope
from ingestion.db.orm import Category, Event, Source, Venue

# (name, slug) — mirrors the 7 categories defined in domain/categories.py (Phase 2).
_CATEGORIES: list[tuple[str, str]] = [
    ("Music", "music"),
    ("Sport", "sport"),
    ("Literature", "literature"),
    ("Education", "education"),
    ("Cinema", "cinema"),
    ("Theatre", "theatre"),
    ("Art", "art"),
]

# (name, city) for a handful of Sofia venues.
_VENUES: list[tuple[str, str]] = [
    ("National Palace of Culture", "Sofia"),
    ("Sofia Opera and Ballet", "Sofia"),
    ("Arena Sofia", "Sofia"),
    ("City Art Gallery", "Sofia"),
    ("Sofia Tech Park", "Sofia"),
]

# (name, type) — seed source rows; types respect the api/scraper check constraint.
_SOURCES: list[tuple[str, str]] = [
    ("seed_local", "scraper"),
    ("seed_api", "api"),
]

_SEED_EVENT_COUNT = 50


def _dedup_key(title: str, start_at: datetime, city: str) -> str:
    return f"{slugify(title)}|{start_at.date().isoformat()}|{slugify(city)}"


async def seed() -> None:
    async with session_scope() as session:
        existing = await session.scalar(select(func.count()).select_from(Event))
        if existing:
            print(f"Seed skipped: events table already has {existing} rows.")
            return

        sources = [Source(name=n, type=t) for n, t in _SOURCES]
        venues = [Venue(name=n, city=c) for n, c in _VENUES]
        categories = [Category(name=n, slug=s) for n, s in _CATEGORIES]
        session.add_all([*sources, *venues, *categories])
        await session.flush()  # assign PKs before building events

        base = datetime.now(UTC).replace(hour=19, minute=0, second=0, microsecond=0)
        events: list[Event] = []
        for i in range(_SEED_EVENT_COUNT):
            category = categories[i % len(categories)]
            venue = venues[i % len(venues)]
            source = sources[i % len(sources)]
            start_at = base + timedelta(days=i)
            title = f"{category.name} Event #{i + 1}"
            events.append(
                Event(
                    source_id=source.id,
                    external_id=f"seed-{i + 1}",
                    title=title,
                    description=f"Sample {category.name.lower()} event for local development.",
                    start_at=start_at,
                    venue_id=venue.id,
                    category_id=category.id,
                    url=f"https://example.com/events/{i + 1}",
                    dedup_key=_dedup_key(title, start_at, venue.city or ""),
                    raw_payload={"seed": True, "index": i + 1},
                )
            )
        session.add_all(events)
        print(
            f"Seeded {len(sources)} sources, {len(venues)} venues, "
            f"{len(categories)} categories, {len(events)} events."
        )


if __name__ == "__main__":
    asyncio.run(seed())
