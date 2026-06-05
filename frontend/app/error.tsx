"use client";

import { ErrorState } from "@/components/states";

// App-level error boundary (within the root layout).
export default function GlobalError({ reset }: { error: Error; reset: () => void }) {
  return (
    <main className="mx-auto max-w-3xl px-6 py-24">
      <ErrorState
        title="Something went wrong"
        message="An unexpected error occurred while loading this page. Please try again."
        retry={reset}
      />
    </main>
  );
}
