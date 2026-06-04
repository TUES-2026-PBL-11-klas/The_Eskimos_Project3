"use client";

import CalendarView from "@/components/CalendarView";
import { EmptyState } from "@/components/states";
import { useDemo } from "@/lib/demo/store";

export default function CalendarPage() {
  const { hydrated, loggedIn, saved } = useDemo();

  if (!hydrated) {
    return (
      <main className="mx-auto max-w-5xl px-6 py-10">
        <div className="skeleton mb-8 h-9 w-48 rounded" />
        <div className="skeleton h-96 w-full rounded-2xl" />
      </main>
    );
  }

  if (!loggedIn) {
    return (
      <main className="mx-auto max-w-5xl px-6 py-20">
        <EmptyState
          icon="🔒"
          title="Log in to see your calendar"
          message="Your calendar shows the events you've marked. Log in to start building it."
          action={{ href: "/login", label: "Log in" }}
        />
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-foreground">Calendar</h1>
        <p className="mt-1 text-sm text-muted">
          {saved.length} marked {saved.length === 1 ? "event" : "events"} across your months.
        </p>
      </header>
      <CalendarView events={saved} />
    </main>
  );
}
