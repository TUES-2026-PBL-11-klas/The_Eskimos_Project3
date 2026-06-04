"use client";

import { ErrorState } from "@/components/states";

export default function EventsError({ reset }: { error: Error; reset: () => void }) {
  return (
    <main className="mx-auto max-w-6xl px-6 py-20">
      <ErrorState
        title="Couldn't load events"
        message="We hit a problem reaching the event service. Please try again."
        retry={reset}
      />
    </main>
  );
}
