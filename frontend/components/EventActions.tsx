"use client";

import type { EventSummary } from "@/lib/api/types";
import { useDemo } from "@/lib/demo/store";
import SaveButton from "./SaveButton";
import RemindButton from "./RemindButton";

// Action row for the detail page: Save toggle, plus a Remind control once the
// event is saved (matches the saved-list behaviour).
export default function EventActions({ event }: { event: EventSummary }) {
  const { loggedIn, isSaved } = useDemo();
  const saved = isSaved(event.id);

  return (
    <div className="flex flex-wrap items-start gap-3">
      <SaveButton event={event} />
      {loggedIn && saved && <RemindButton event={event} />}
    </div>
  );
}
