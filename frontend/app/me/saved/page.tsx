"use client";

import Link from "next/link";

import RemindButton from "@/components/RemindButton";
import { EmptyState, EventListSkeleton } from "@/components/states";
import { categoryStyle } from "@/lib/categories";
import { useDemo } from "@/lib/demo/store";
import { formatDate, formatTime, relativeDay } from "@/lib/format";

export default function SavedPage() {
  const { hydrated, loggedIn, saved, unsave } = useDemo();

  if (!hydrated) {
    return (
      <main className="mx-auto max-w-4xl px-6 py-10">
        <div className="skeleton mb-8 h-9 w-48 rounded" />
        <EventListSkeleton count={4} />
      </main>
    );
  }

  if (!loggedIn) {
    return (
      <main className="mx-auto max-w-4xl px-6 py-20">
        <EmptyState
          icon="🔒"
          title="Log in to see your saved events"
          message="Saved events are tied to your account. Log in to mark events and build your list."
          action={{ href: "/login", label: "Log in" }}
        />
      </main>
    );
  }

  // Sorted by start_at (mirrors GET /me/saved).
  const items = [...saved].sort((a, b) => a.start_at.localeCompare(b.start_at));

  return (
    <main className="mx-auto max-w-4xl px-6 py-10">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-foreground">Saved events</h1>
        <p className="mt-1 text-sm text-muted">
          {items.length} {items.length === 1 ? "event" : "events"} marked — sorted by date.
        </p>
      </header>

      {items.length === 0 ? (
        <EmptyState
          icon="☆"
          title="No saved events yet"
          message="Browse events and tap Save to keep them here."
          action={{ href: "/events", label: "Browse events" }}
        />
      ) : (
        <ul className="space-y-4">
          {items.map((event) => {
            const style = categoryStyle(event.category);
            return (
              <li
                key={event.id}
                className="rounded-2xl border border-border bg-surface p-5"
                style={{ borderLeft: `3px solid ${style.accent}` }}
              >
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div className="min-w-0">
                    <div className="mb-2 flex items-center gap-2">
                      {event.category && (
                        <span
                          className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium"
                          style={{ background: style.tint, color: style.accent }}
                        >
                          {style.icon} {event.category}
                        </span>
                      )}
                      <span className="text-xs text-muted">{relativeDay(event.start_at)}</span>
                    </div>
                    <Link
                      href={`/events/${event.id}`}
                      className="text-lg font-semibold text-foreground hover:text-accent-hover"
                    >
                      {event.title}
                    </Link>
                    <div className="mt-2 flex flex-col gap-1 text-sm text-muted">
                      <span>🗓️ {formatDate(event.start_at)} · {formatTime(event.start_at)}</span>
                      {event.venue && (
                        <span>
                          📍 {event.venue.name}
                          {event.venue.city ? `, ${event.venue.city}` : ""}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="flex flex-col items-end gap-2">
                    <RemindButton event={event} />
                    <button
                      type="button"
                      onClick={() => unsave(event.id)}
                      className="text-sm font-medium text-muted transition hover:text-danger"
                    >
                      Remove
                    </button>
                  </div>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </main>
  );
}
