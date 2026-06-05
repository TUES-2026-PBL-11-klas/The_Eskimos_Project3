"""add event_id to saved_events; fix user_preferences.timezone default

1. Adds ``saved_events.event_id`` — the originating events-DB id at save-time
   (nullable; no cross-DB FK). Lets the frontend map an event to its saved record
   for the save/unsave toggle. Existing rows keep NULL (re-enrichable via
   (source, external_id)).

2. Fixes ``user_preferences.timezone`` whose default in migration 0001 was the
   already-quoted string ``'Europe/Sofia'``; SQLAlchemy SQL-quoted it again, so the
   DDL default became ``'''Europe/Sofia'''`` and every row stored the literal value
   WITH surrounding quotes. Reset the default and strip the quotes from existing rows.

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-05
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
    op.add_column(
        "saved_events",
        sa.Column("event_id", sa.Integer(), nullable=True),
    )
    # Correct the timezone default and strip the erroneously-stored surrounding quotes.
    op.alter_column(
        "user_preferences",
        "timezone",
        server_default=sa.text("'Europe/Sofia'"),
    )
    op.execute("UPDATE user_preferences SET timezone = trim(both '''' from timezone)")


def downgrade() -> None:
    op.alter_column(
        "user_preferences",
        "timezone",
        server_default=sa.text("'''Europe/Sofia'''"),
    )
    op.drop_column("saved_events", "event_id")
