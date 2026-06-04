import type { EventSummary } from "@/lib/api/types";
import EventCard from "./EventCard";
import { EmptyState } from "./states";

// Responsive grid: 3-col desktop / 2-col tablet / 1-col mobile.
export default function EventList({
  events,
  emptyTitle = "No events found",
  emptyMessage = "Try adjusting your filters or check back soon.",
}: {
  events: EventSummary[];
  emptyTitle?: string;
  emptyMessage?: string;
}) {
  if (events.length === 0) {
    return <EmptyState title={emptyTitle} message={emptyMessage} />;
  }

  return (
    <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
      {events.map((event) => (
        <EventCard key={event.id} event={event} />
      ))}
    </div>
  );
}
