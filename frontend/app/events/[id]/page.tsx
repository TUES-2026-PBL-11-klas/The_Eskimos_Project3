import Link from "next/link";
import { notFound } from "next/navigation";
import type { Metadata } from "next";

import EventDetails from "@/components/EventDetails";
import { getEvent } from "@/lib/api/endpoints";
import { ApiError } from "@/lib/api/types";

type Params = Promise<{ id: string }>;

async function loadEvent(id: string) {
  try {
    return await getEvent(id);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) notFound();
    throw err;
  }
}

export async function generateMetadata({ params }: { params: Params }): Promise<Metadata> {
  const { id } = await params;
  try {
    const event = await getEvent(id);
    return { title: event.title };
  } catch {
    return { title: "Event" };
  }
}

export default async function EventDetailPage({ params }: { params: Params }) {
  const { id } = await params;
  const event = await loadEvent(id);

  return (
    <main className="mx-auto max-w-3xl px-6 py-10">
      <Link
        href="/events"
        className="mb-6 inline-flex items-center gap-1 text-sm text-muted transition hover:text-foreground"
      >
        ← Back to events
      </Link>
      <EventDetails event={event} />
    </main>
  );
}
