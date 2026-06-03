"""SQLAlchemy 2.0 typed ORM models for the events schema.

This service is the sole owner and writer of these tables. Relationships default to
SQLAlchemy's lazy loading; hot read paths in the repository opt into eager loading
(`selectinload`) explicitly — see repository/event_repository.py (Phase 2).

All timestamps are timezone-aware UTC (`TIMESTAMPTZ` via DateTime(timezone=True)).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Source(Base):
    __tablename__ = "sources"
    __table_args__ = (CheckConstraint("type IN ('api', 'scraper')", name="ck_sources_type"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    type: Mapped[str] = mapped_column(String(16))
    base_url: Mapped[str | None] = mapped_column(String(500))
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    events: Mapped[list[Event]] = relationship(back_populates="source")


class Venue(Base):
    __tablename__ = "venues"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(120))

    events: Mapped[list[Event]] = relationship(back_populates="venue")


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    slug: Mapped[str] = mapped_column(String(100), unique=True)

    events: Mapped[list[Event]] = relationship(back_populates="category")


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        # Within-source idempotency for upserts.
        UniqueConstraint("source_id", "external_id", name="uq_events_source_external"),
        # Time-range queries.
        Index("ix_events_start_at", "start_at"),
        # Category + time browse path.
        Index("ix_events_category_start_at", "category_id", "start_at"),
        # Cross-source dedup lookup (Phase 2 Deduplicator.find_duplicate) — indexed, not a scan.
        Index("ix_events_dedup_key", "dedup_key"),
        # Fuzzy title search via pg_trgm (extension + ops created in the migration).
        Index(
            "ix_events_title_trgm",
            "title",
            postgresql_using="gin",
            postgresql_ops={"title": "gin_trgm_ops"},
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"))
    external_id: Mapped[str] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    venue_id: Mapped[int | None] = mapped_column(ForeignKey("venues.id"))
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"))
    url: Mapped[str] = mapped_column(String(1000))
    dedup_key: Mapped[str] = mapped_column(String(500))
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    source: Mapped[Source] = relationship(back_populates="events")
    venue: Mapped[Venue | None] = relationship(back_populates="events")
    category: Mapped[Category | None] = relationship(back_populates="events")
