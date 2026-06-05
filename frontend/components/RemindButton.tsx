"use client";

import { useState } from "react";

import type { EventSummary } from "@/lib/api/types";
import { useDemo } from "@/lib/demo/store";

// Shown on a saved event. Creates a reminder using the user's default_lead_hours
// (no body), and surfaces the API's "too soon" rejection. Real app: POST
// /me/saved/{id}/reminder; here it updates the demo store.
export default function RemindButton({
  event,
  className = "",
}: {
  event: EventSummary;
  className?: string;
}) {
  const { addReminder, reminderFor } = useDemo();
  const existing = reminderFor(event.id);
  const [error, setError] = useState("");

  if (existing) {
    return (
      <span
        className={`inline-flex items-center gap-2 rounded-lg border border-success/40 bg-success/10 px-5 py-2.5 text-sm font-semibold text-success ${className}`}
      >
        🔔 Reminder set
      </span>
    );
  }

  return (
    <div className="flex flex-col gap-1.5">
      <button
        type="button"
        onClick={async () => {
          const res = await addReminder(event);
          setError(res.ok ? "" : (res.error ?? "Couldn't set a reminder."));
        }}
        className={`inline-flex items-center gap-2 rounded-lg border border-border bg-surface px-5 py-2.5 text-sm font-semibold text-foreground transition hover:border-accent ${className}`}
      >
        🔔 Remind me
      </button>
      {error && <p className="text-sm text-danger">{error}</p>}
    </div>
  );
}
