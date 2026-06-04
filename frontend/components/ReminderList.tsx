"use client";

import Link from "next/link";

import type { ReminderStatus } from "@/lib/api/types";
import { useDemo } from "@/lib/demo/store";
import { formatDateTime } from "@/lib/format";

const STATUS_STYLE: Record<ReminderStatus, string> = {
  pending: "border-accent/40 bg-accent/10 text-accent",
  sent: "border-success/40 bg-success/10 text-success",
  cancelled: "border-border bg-surface-2 text-muted",
};

// Lists this user's reminders with status + a cancel action for pending ones.
// Mirrors GET /me/reminders and DELETE /me/reminders/{id}.
export default function ReminderList() {
  const { reminders, cancelReminder, dueReminders } = useDemo();
  const dueIds = new Set(dueReminders().map((r) => r.id));

  // Pending first, then by remind time.
  const ordered = [...reminders].sort((a, b) => {
    if (a.status !== b.status) return a.status === "pending" ? -1 : 1;
    return a.remind_at.localeCompare(b.remind_at);
  });

  if (ordered.length === 0) {
    return (
      <p className="rounded-xl border border-dashed border-border bg-surface-2 px-4 py-6 text-center text-sm text-muted">
        No reminders yet. Open a saved event and tap “Remind me”.
      </p>
    );
  }

  return (
    <ul className="space-y-3">
      {ordered.map((r) => {
        const due = dueIds.has(r.id);
        return (
          <li
            key={r.id}
            className="flex items-center justify-between gap-4 rounded-xl border border-border bg-surface-2 p-4"
          >
            <div className="min-w-0">
              <Link
                href={`/events/${r.event_id}`}
                className="font-medium text-foreground hover:text-accent-hover"
              >
                {r.event_title}
              </Link>
              <p className="mt-1 text-xs text-muted">
                Reminder at {formatDateTime(r.remind_at)}
              </p>
            </div>

            <div className="flex shrink-0 items-center gap-3">
              <span
                className={`rounded-full border px-2.5 py-0.5 text-xs font-medium capitalize ${STATUS_STYLE[r.status]}`}
              >
                {due ? "due" : r.status}
              </span>
              {r.status === "pending" && (
                <button
                  type="button"
                  onClick={() => cancelReminder(r.id)}
                  className="text-sm font-medium text-muted transition hover:text-danger"
                >
                  Cancel
                </button>
              )}
            </div>
          </li>
        );
      })}
    </ul>
  );
}
