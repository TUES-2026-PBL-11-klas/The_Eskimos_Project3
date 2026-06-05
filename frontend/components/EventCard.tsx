import Link from "next/link";

import type { EventSummary } from "@/lib/api/types";
import { categoryStyle } from "@/lib/categories";
import { formatDate, formatTime, relativeDay } from "@/lib/format";

// Per D2: title, date/time (start only), venue, category. No price, no end time.
export default function EventCard({ event }: { event: EventSummary }) {
  const style = categoryStyle(event.category);

  return (
    <Link
      href={`/events/${event.id}`}
      className="group flex flex-col rounded-2xl border border-border bg-surface p-5 transition hover:-translate-y-0.5 hover:border-accent/60 hover:bg-surface-2"
      style={{ borderLeft: `3px solid ${style.accent}` }}
    >
      <div className="mb-3 flex items-center justify-between gap-2">
        {event.category && (
          <span
            className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium"
            style={{ background: style.tint, color: style.accent }}
          >
            <span aria-hidden>{style.icon}</span>
            {event.category}
          </span>
        )}
        <span className="text-xs font-medium text-muted">{relativeDay(event.start_at)}</span>
      </div>

      <h3 className="text-lg font-semibold leading-snug text-foreground transition group-hover:text-accent-hover">
        {event.title}
      </h3>

      <div className="mt-4 flex flex-col gap-1.5 text-sm text-muted">
        <span className="flex items-center gap-2">
          <span aria-hidden>🗓️</span>
          {formatDate(event.start_at)} · {formatTime(event.start_at)}
        </span>
        {event.venue && (
          <span className="flex items-center gap-2">
            <span aria-hidden>📍</span>
            {event.venue.name}
            {event.venue.city ? `, ${event.venue.city}` : ""}
          </span>
        )}
      </div>
    </Link>
  );
}
