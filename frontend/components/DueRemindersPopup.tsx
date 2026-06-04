"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import type { Reminder } from "@/lib/api/types";
import { useDemo } from "@/lib/demo/store";
import { formatDate, formatTime } from "@/lib/format";

// Mounted in the app layout. For a logged-in user it checks due reminders ONCE on
// load (D6 — single GET /me/reminders/due, no polling loop) and shows a toast if
// any are due. Dismissable; does not reappear until the next load.
export default function DueRemindersPopup() {
  const { hydrated, loggedIn, dueReminders } = useDemo();
  const [due, setDue] = useState<Reminder[]>([]);
  const [dismissed, setDismissed] = useState(false);
  const [checked, setChecked] = useState(false);

  // Single check once, after hydration, for a logged-in user.
  /* eslint-disable react-hooks/set-state-in-effect */
  useEffect(() => {
    if (!hydrated || checked) return;
    setChecked(true);
    if (loggedIn) setDue(dueReminders());
  }, [hydrated, checked, loggedIn, dueReminders]);
  /* eslint-enable react-hooks/set-state-in-effect */

  if (!loggedIn || dismissed || due.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 w-[22rem] max-w-[calc(100vw-2rem)] rounded-2xl border border-accent/40 bg-surface p-5 shadow-2xl">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="text-xl">🔔</span>
          <h3 className="font-semibold text-foreground">
            {due.length} event{due.length === 1 ? "" : "s"} coming up
          </h3>
        </div>
        <button
          onClick={() => setDismissed(true)}
          aria-label="Dismiss"
          className="text-muted transition hover:text-foreground"
        >
          ✕
        </button>
      </div>

      <ul className="mt-3 space-y-2">
        {due.slice(0, 3).map((r) => (
          <li key={r.id} className="text-sm">
            <Link
              href={`/events/${r.event_id}`}
              className="font-medium text-foreground hover:text-accent-hover"
            >
              {r.event_title}
            </Link>
            <span className="block text-xs text-muted">
              {formatDate(r.start_at)} · {formatTime(r.start_at)}
            </span>
          </li>
        ))}
      </ul>

      <Link
        href="/me"
        onClick={() => setDismissed(true)}
        className="mt-4 inline-block text-sm font-semibold text-accent hover:text-accent-hover"
      >
        View all reminders →
      </Link>
    </div>
  );
}
