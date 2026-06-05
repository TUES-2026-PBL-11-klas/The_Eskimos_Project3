import type { Metadata } from "next";

import EventList from "@/components/EventList";
import FilterBar from "@/components/FilterBar";
import Pagination from "@/components/Pagination";
import { getCategories, getEvents, getVenues } from "@/lib/api/endpoints";
import type { EventFilters } from "@/lib/api/types";

export const metadata: Metadata = { title: "All events" };

type SearchParams = Promise<Record<string, string | string[] | undefined>>;

function one(v: string | string[] | undefined): string | undefined {
  return Array.isArray(v) ? v[0] : v;
}

export default async function EventsPage({ searchParams }: { searchParams: SearchParams }) {
  const sp = await searchParams;

  const filters: EventFilters = {
    page: Number(one(sp.page)) || 1,
    category: one(sp.category),
    city: one(sp.city),
    venue_id: one(sp.venue_id),
    q: one(sp.q),
    date_from: one(sp.date_from),
  };

  const [result, categories, venues] = await Promise.all([
    getEvents(filters),
    getCategories(),
    getVenues(),
  ]);
  const cities = [...new Set(venues.map((v) => v.city).filter(Boolean))].sort() as string[];

  // The URL carries the category slug (the API's filter key); resolve it back to
  // the display name for the heading.
  const activeCategoryName = filters.category
    ? (categories.find((c) => c.slug === filters.category)?.name ?? filters.category)
    : undefined;

  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <header className="mb-6">
        <h1 className="text-3xl font-bold text-foreground">
          {activeCategoryName ? `${activeCategoryName} events` : "All events"}
        </h1>
        <p className="mt-1 text-sm text-muted">
          {result.total} {result.total === 1 ? "event" : "events"}
          {filters.city ? ` in ${filters.city}` : ""}
          {filters.q ? ` matching “${filters.q}”` : ""}
        </p>
      </header>

      <FilterBar categories={categories} cities={cities} venues={venues} />

      <div className="mt-8">
        <EventList events={result.items} />
        <Pagination page={result.page} pages={result.pages} />
      </div>
    </main>
  );
}
