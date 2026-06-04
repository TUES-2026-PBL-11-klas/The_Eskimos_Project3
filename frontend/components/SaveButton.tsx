"use client";

import Link from "next/link";

import type { EventSummary } from "@/lib/api/types";
import { useDemo } from "@/lib/demo/store";

// Login-gated save toggle (D5: no anonymous favourites). Logged-out → prompts
// login; logged-in → toggles saved state. In the real app this calls the
// /me/saved route handler; here it updates the demo store.
export default function SaveButton({
  event,
  className = "",
}: {
  event: EventSummary;
  className?: string;
}) {
  const { loggedIn, isSaved, toggleSave } = useDemo();
  const saved = isSaved(event.id);

  if (!loggedIn) {
    return (
      <Link
        href="/login"
        className={`inline-flex items-center gap-2 rounded-lg border border-border bg-surface px-5 py-2.5 text-sm font-semibold text-foreground transition hover:border-accent ${className}`}
      >
        ☆ Log in to save
      </Link>
    );
  }

  return (
    <button
      type="button"
      onClick={() => toggleSave(event)}
      aria-pressed={saved}
      className={`inline-flex items-center gap-2 rounded-lg px-5 py-2.5 text-sm font-semibold transition ${
        saved
          ? "border border-accent bg-accent/15 text-accent hover:bg-accent/25"
          : "border border-border bg-surface text-foreground hover:border-accent"
      } ${className}`}
    >
      {saved ? "★ Saved" : "☆ Save"}
    </button>
  );
}
