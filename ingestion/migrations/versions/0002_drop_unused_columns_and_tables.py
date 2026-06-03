"""drop unused columns and tables

Trims the schema to what the live sources actually populate. Removed because they were
100% NULL / unused in practice:
  * events.end_at        — no source exposes an event end time
  * events.price_min/max/currency — dropped per product decision (sparse, low value)
  * venues.address/lat/lon — never populated by any scraper
  * tags + event_tags    — the M:N tagging feature was never wired up (0 rows)

`description` and `venue_id` are kept: partially populated, but with real data.

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-30
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Drop the unused tagging tables (event_tags first — it FKs both events and tags).
    op.drop_table("event_tags")
    op.drop_table("tags")

    # Drop fully-NULL / decommissioned event columns.
    op.drop_column("events", "end_at")
    op.drop_column("events", "price_min")
    op.drop_column("events", "price_max")
    op.drop_column("events", "currency")

    # Drop never-populated venue columns (table itself stays: id, name, city).
    op.drop_column("venues", "address")
    op.drop_column("venues", "lat")
    op.drop_column("venues", "lon")


def downgrade() -> None:
    # Recreate venue columns (nullable — original data is not restorable).
    op.add_column("venues", sa.Column("lon", sa.Numeric(precision=9, scale=6), nullable=True))
    op.add_column("venues", sa.Column("lat", sa.Numeric(precision=9, scale=6), nullable=True))
    op.add_column("venues", sa.Column("address", sa.String(length=500), nullable=True))

    # Recreate event columns.
    op.add_column("events", sa.Column("currency", sa.String(length=3), nullable=True))
    op.add_column(
        "events", sa.Column("price_max", sa.Numeric(precision=10, scale=2), nullable=True)
    )
    op.add_column(
        "events", sa.Column("price_min", sa.Numeric(precision=10, scale=2), nullable=True)
    )
    op.add_column("events", sa.Column("end_at", sa.DateTime(timezone=True), nullable=True))

    # Recreate the tagging tables. New tables created by the owner inherit the
    # events_reader SELECT grant via the ALTER DEFAULT PRIVILEGES set in migration 0001.
    op.create_table(
        "tags",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.UniqueConstraint("slug", name="uq_tags_slug"),
    )
    op.create_table(
        "event_tags",
        sa.Column("event_id", sa.Integer(), primary_key=True),
        sa.Column("tag_id", sa.Integer(), primary_key=True),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], ondelete="CASCADE"),
    )
