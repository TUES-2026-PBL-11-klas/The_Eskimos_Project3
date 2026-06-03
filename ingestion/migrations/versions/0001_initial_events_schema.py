"""initial events schema

Creates the events schema this service owns (sources, venues, categories, tags, events,
event_tags), all indexes/constraints, the pg_trgm extension + GIN trigram index on
events.title, and the SELECT-only `events_reader` role for the downstream read-only API.

Revision ID: 0001
Revises:
Create Date: 2026-05-30
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # pg_trgm powers the fuzzy GIN index on events.title (created below).
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.create_table(
        "sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("type", sa.String(length=16), nullable=False),
        sa.Column("base_url", sa.String(length=500), nullable=True),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("name", name="uq_sources_name"),
        sa.CheckConstraint("type IN ('api', 'scraper')", name="ck_sources_type"),
    )

    op.create_table(
        "venues",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("address", sa.String(length=500), nullable=True),
        sa.Column("city", sa.String(length=120), nullable=True),
        sa.Column("lat", sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column("lon", sa.Numeric(precision=9, scale=6), nullable=True),
    )

    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.UniqueConstraint("slug", name="uq_categories_slug"),
    )

    op.create_table(
        "tags",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.UniqueConstraint("slug", name="uq_tags_slug"),
    )

    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("venue_id", sa.Integer(), nullable=True),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("price_min", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("price_max", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=True),
        sa.Column("url", sa.String(length=1000), nullable=False),
        # dedup_key: deterministic cross-source identity string; B-tree index below makes
        # the Deduplicator's find_duplicate an indexed lookup instead of a full scan.
        sa.Column("dedup_key", sa.String(length=500), nullable=False),
        sa.Column("raw_payload", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["venue_id"], ["venues.id"]),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"]),
        sa.UniqueConstraint("source_id", "external_id", name="uq_events_source_external"),
    )
    op.create_index("ix_events_start_at", "events", ["start_at"])
    op.create_index("ix_events_category_start_at", "events", ["category_id", "start_at"])
    op.create_index("ix_events_dedup_key", "events", ["dedup_key"])
    op.create_index(
        "ix_events_title_trgm",
        "events",
        ["title"],
        postgresql_using="gin",
        postgresql_ops={"title": "gin_trgm_ops"},
    )

    op.create_table(
        "event_tags",
        sa.Column("event_id", sa.Integer(), primary_key=True),
        sa.Column("tag_id", sa.Integer(), primary_key=True),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], ondelete="CASCADE"),
    )

    # Read-only role for the downstream API. NOLOGIN + SELECT-only — the database enforces
    # the read boundary. The API's deployment attaches a login role inheriting this one and
    # supplies credentials at runtime, so no password lives in git.
    # Idempotent: events_reader is a cluster-wide role, so it may already exist if another
    # database in the same cluster ran this migration (e.g. a test DB alongside dev).
    op.execute(
        "DO $$ BEGIN "
        "IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'events_reader') "
        "THEN CREATE ROLE events_reader NOLOGIN; END IF; "
        "END $$"
    )
    op.execute("GRANT USAGE ON SCHEMA public TO events_reader")
    op.execute("GRANT SELECT ON ALL TABLES IN SCHEMA public TO events_reader")
    op.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO events_reader")


def downgrade() -> None:
    op.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE SELECT ON TABLES FROM events_reader"
    )
    op.execute("REVOKE SELECT ON ALL TABLES IN SCHEMA public FROM events_reader")
    op.execute("REVOKE USAGE ON SCHEMA public FROM events_reader")
    op.execute("DROP ROLE IF EXISTS events_reader")

    op.drop_table("event_tags")
    op.drop_index("ix_events_title_trgm", table_name="events")
    op.drop_index("ix_events_dedup_key", table_name="events")
    op.drop_index("ix_events_category_start_at", table_name="events")
    op.drop_index("ix_events_start_at", table_name="events")
    op.drop_table("events")
    op.drop_table("tags")
    op.drop_table("categories")
    op.drop_table("venues")
    op.drop_table("sources")

    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
