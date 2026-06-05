"""SQLAlchemy ORM for the users database.

Five tables:
  users            — account, bcrypt password hash
  user_preferences — per-user defaults (1-to-1, created on register)
  sessions         — opaque bearer tokens stored as SHA-256 hashes
  saved_events     — snapshot of an event the user saved (no FK to events DB)
  reminders        — optional reminder per saved event, with a status enum

The snapshot pattern in ``saved_events`` (denormalised title/start_at/venue/url)
is intentional: it decouples the users DB from the events DB so saves survive
ingestion re-runs or event deletions without any cross-DB query.

``UsersBase`` is a separate ``DeclarativeBase`` so it never touches the events schema
or triggers accidental migrations against the events DB.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class UsersBase(DeclarativeBase):
    pass


class User(UsersBase):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    preferences: Mapped[UserPreferences | None] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    sessions: Mapped[list[Session]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    saved_events: Mapped[list[SavedEvent]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class UserPreferences(UsersBase):
    __tablename__ = "user_preferences"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    default_lead_hours: Mapped[int] = mapped_column(Integer(), server_default="24")
    # NB: SQLAlchemy SQL-quotes string server_defaults, so the value must be unquoted
    # here (an inner quote would be double-quoted into the stored data — see migration 0002).
    timezone: Mapped[str] = mapped_column(String(50), server_default="Europe/Sofia")

    user: Mapped[User] = relationship(back_populates="preferences")


class Session(UsersBase):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    token_hash: Mapped[str] = mapped_column(String(255), unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    user_agent: Mapped[str | None] = mapped_column(String(500))

    user: Mapped[User] = relationship(back_populates="sessions")


class SavedEvent(UsersBase):
    __tablename__ = "saved_events"
    __table_args__ = (
        UniqueConstraint("user_id", "source", "external_id", name="uq_saved_user_source_ext"),
        Index("ix_saved_events_user_start_at", "user_id", "start_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    source: Mapped[str] = mapped_column(String(100))
    external_id: Mapped[str] = mapped_column(String(255))
    # The originating events-DB id at save-time. Nullable (no cross-DB FK); lets
    # the frontend map an event to its saved record for the save/unsave toggle.
    event_id: Mapped[int | None] = mapped_column(Integer())
    # Snapshot fields — intentionally denormalised; no FK to the events DB.
    title: Mapped[str] = mapped_column(String(500))
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    venue_name: Mapped[str | None] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(120))
    category: Mapped[str | None] = mapped_column(String(100))
    url: Mapped[str] = mapped_column(String(1000))
    saved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped[User] = relationship(back_populates="saved_events")
    reminders: Mapped[list[Reminder]] = relationship(
        back_populates="saved_event", cascade="all, delete-orphan"
    )


class Reminder(UsersBase):
    __tablename__ = "reminders"
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'cancelled')", name="ck_reminders_status"),
        Index("ix_reminders_status_remind_at", "status", "remind_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    saved_event_id: Mapped[int] = mapped_column(
        ForeignKey("saved_events.id", ondelete="CASCADE")
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    remind_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(10), server_default="'pending'")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    saved_event: Mapped[SavedEvent] = relationship(back_populates="reminders")
