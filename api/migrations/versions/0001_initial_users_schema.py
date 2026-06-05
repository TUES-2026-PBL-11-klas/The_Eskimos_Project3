"""initial users schema

Creates every table this service owns: users, user_preferences, sessions,
saved_events, and reminders, along with all constraints and indexes.

Snapshot denormalisation rationale (saved_events.title/start_at/venue_name/url):
  The users DB has no foreign key to the events DB — they are separate Postgres
  instances. Snapshotting display fields at save-time means:
  (a) A user's saved-event list survives ingestion re-runs, dedup merges, or
      source deletions without any cross-DB JOIN or compensating job.
  (b) The calendar and reminder endpoints need no events-DB read at all.
  The (source, external_id) pair is kept for optional re-enrichment (Phase 7).

Indexes created:
  - users.email UNIQUE (login lookup)
  - sessions.token_hash UNIQUE (authentication lookup — every request)
  - saved_events (user_id, source, external_id) UNIQUE (idempotent save)
  - saved_events (user_id, start_at) (calendar range queries)
  - reminders (status, remind_at) (due-polling: WHERE status='pending' AND remind_at <= now())

Revision ID: 0001
Revises:
Create Date: 2026-06-04
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=True),
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
        sa.UniqueConstraint("email", name="uq_users_email"),
    )

    op.create_table(
        "user_preferences",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("default_lead_hours", sa.Integer(), server_default="24", nullable=False),
        sa.Column(
            "timezone", sa.String(50), server_default="'Europe/Sofia'", nullable=False
        ),
        sa.UniqueConstraint("user_id", name="uq_user_preferences_user_id"),
    )

    op.create_table(
        "sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.UniqueConstraint("token_hash", name="uq_sessions_token_hash"),
    )

    op.create_table(
        "saved_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source", sa.String(100), nullable=False),
        sa.Column("external_id", sa.String(255), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("venue_name", sa.String(255), nullable=True),
        sa.Column("city", sa.String(120), nullable=True),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("url", sa.String(1000), nullable=False),
        sa.Column(
            "saved_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "user_id", "source", "external_id", name="uq_saved_user_source_ext"
        ),
    )
    op.create_index(
        "ix_saved_events_user_start_at", "saved_events", ["user_id", "start_at"]
    )

    op.create_table(
        "reminders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "saved_event_id",
            sa.Integer(),
            sa.ForeignKey("saved_events.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("remind_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(10), server_default="'pending'", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'cancelled')", name="ck_reminders_status"
        ),
    )
    op.create_index("ix_reminders_status_remind_at", "reminders", ["status", "remind_at"])


def downgrade() -> None:
    op.drop_index("ix_reminders_status_remind_at", table_name="reminders")
    op.drop_table("reminders")
    op.drop_index("ix_saved_events_user_start_at", table_name="saved_events")
    op.drop_table("saved_events")
    op.drop_table("sessions")
    op.drop_table("user_preferences")
    op.drop_table("users")
