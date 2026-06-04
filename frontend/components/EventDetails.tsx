import type { EventDetail } from "@/lib/api/types";
import { categoryStyle } from "@/lib/categories";
import { formatDate, formatTime, relativeDay } from "@/lib/format";
import EventActions from "./EventActions";

// Detail layout. Per D2: start time + venue + category + source link only —
// no price, no end time. The save / remind controls arrive in Phase 6; for now
// a login-gated placeholder hints at the logged-in experience.
export default function EventDetails({ event }: { event: EventDetail }) {
  const style = categoryStyle(event.category);

  return (
    <article className="overflow-hidden rounded-2xl border border-border bg-surface">
      <div className="h-1.5 w-full" style={{ background: style.accent }} />

      <div className="p-6 sm:p-8">
        <div className="mb-4 flex flex-wrap items-center gap-3">
          {event.category && (
            <span
              className="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-medium"
              style={{ background: style.tint, color: style.accent }}
            >
              <span aria-hidden>{style.icon}</span>
              {event.category}
            </span>
          )}
          <span className="rounded-full bg-surface-2 px-3 py-1 text-sm text-muted">
            {relativeDay(event.start_at)}
          </span>
        </div>

        <h1 className="text-3xl font-bold leading-tight text-foreground sm:text-4xl">
          {event.title}
        </h1>

        {event.description && (
          <p className="mt-4 max-w-2xl leading-relaxed text-muted">{event.description}</p>
        )}

        <dl className="mt-8 grid gap-4 sm:grid-cols-2">
          <div className="rounded-xl border border-border bg-surface-2 p-4">
            <dt className="text-xs uppercase tracking-wide text-muted">Date &amp; time</dt>
            <dd className="mt-1 font-semibold text-foreground">
              {formatDate(event.start_at)}
              <span className="text-muted"> · </span>
              {formatTime(event.start_at)}
            </dd>
          </div>

          {event.venue && (
            <div className="rounded-xl border border-border bg-surface-2 p-4">
              <dt className="text-xs uppercase tracking-wide text-muted">Venue</dt>
              <dd className="mt-1 font-semibold text-foreground">
                {event.venue.name}
                {event.venue.city && (
                  <span className="block text-sm font-normal text-muted">{event.venue.city}</span>
                )}
              </dd>
            </div>
          )}
        </dl>

        <div className="mt-8 flex flex-wrap items-start gap-3">
          <EventActions event={event} />
        </div>
      </div>
    </article>
  );
}
