"""Read-only SQLAlchemy ORM mapping for the events database.

This service does not own these tables — the ingestion service is the sole writer. The models
here are mapped against the schema as it exists after migration 0002 (the trimmed shape): no
``end_at``, no price columns, no tags / event_tags. No ``Base.metadata`` migrations are run
from this package; Alembic is used only for the users database.

The ``EventsBase`` uses its own ``DeclarativeBase`` so it never collides with the users models
or triggers accidental schema operations against the events DB.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class EventsBase(DeclarativeBase):
    pass


class Source(EventsBase):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    type: Mapped[str] = mapped_column(String(16))
    base_url: Mapped[str | None] = mapped_column(String(500))
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    events: Mapped[list[Event]] = relationship(back_populates="source")


class Venue(EventsBase):
    __tablename__ = "venues"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(120))

    events: Mapped[list[Event]] = relationship(back_populates="venue")


class Category(EventsBase):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    slug: Mapped[str] = mapped_column(String(100))

    events: Mapped[list[Event]] = relationship(back_populates="category")


class Event(EventsBase):
    __tablename__ = "events"
    __table_args__ = (
        UniqueConstraint("source_id", "external_id", name="uq_events_source_external"),
        Index("ix_events_start_at", "start_at"),
        Index("ix_events_category_start_at", "category_id", "start_at"),
        Index("ix_events_dedup_key", "dedup_key"),
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
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    source: Mapped[Source] = relationship(back_populates="events")
    venue: Mapped[Venue | None] = relationship(back_populates="events")
    category: Mapped[Category | None] = relationship(back_populates="events")
