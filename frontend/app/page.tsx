import Link from "next/link";

import CategoryGrid from "@/components/CategoryGrid";
import EventList from "@/components/EventList";
import { getCategories, getStats, getUpcoming } from "@/lib/api/endpoints";

// Render per request so the data source (mock vs live API) is honoured at runtime
// rather than baked in at build time.
export const dynamic = "force-dynamic";

export default async function HomePage() {
  const [stats, categories, upcoming] = await Promise.all([
    getStats(),
    getCategories(),
    getUpcoming(6),
  ]);

  const statItems = [
    { label: "Events", value: stats.total_events },
    { label: "Upcoming", value: stats.upcoming_events },
    { label: "Categories", value: stats.total_categories },
    { label: "Venues", value: stats.total_venues },
  ];

  return (
    <main className="mx-auto max-w-6xl px-6">
      {/* Hero */}
      <section className="py-16 text-center sm:py-24">
        <span className="inline-block rounded-full border border-border bg-surface px-3 py-1 text-xs font-medium text-muted">
          One place for everything happening near you
        </span>
        <h1 className="mx-auto mt-5 max-w-3xl text-4xl font-bold tracking-tight text-foreground sm:text-6xl">
          Discover events across{" "}
          <span className="text-accent">Bulgaria</span>
        </h1>
        <p className="mx-auto mt-5 max-w-xl text-lg text-muted">
          Concerts, tech meetups, theatre, sports and more — aggregated from across the web,
          searchable in one place.
        </p>

        <form action="/search" className="mx-auto mt-8 flex max-w-lg gap-2">
          <input
            name="q"
            type="search"
            placeholder="Search events, e.g. “jazz”, “rust”, “festival”…"
            className="w-full rounded-xl border border-border bg-surface px-4 py-3 text-foreground placeholder:text-muted focus:border-accent focus:outline-none"
          />
          <button
            type="submit"
            className="rounded-xl bg-accent px-5 py-3 font-semibold text-white transition hover:bg-accent-hover"
          >
            Search
          </button>
        </form>

        <div className="mx-auto mt-12 grid max-w-2xl grid-cols-2 gap-4 sm:grid-cols-4">
          {statItems.map((s) => (
            <div key={s.label} className="rounded-2xl border border-border bg-surface px-4 py-5">
              <div className="text-3xl font-bold text-foreground">{s.value}</div>
              <div className="mt-1 text-sm text-muted">{s.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Near (upcoming) events */}
      <section className="py-8">
        <div className="mb-6 flex items-end justify-between">
          <div>
            <h2 className="text-2xl font-bold text-foreground">Happening soon</h2>
            <p className="mt-1 text-sm text-muted">The nearest events by date.</p>
          </div>
          <Link href="/events" className="text-sm font-semibold text-accent hover:text-accent-hover">
            See all events →
          </Link>
        </div>
        <EventList
          events={upcoming}
          emptyTitle="Nothing coming up"
          emptyMessage="There are no upcoming events right now — check back soon."
        />
      </section>

      {/* Categories */}
      <section className="py-12">
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-foreground">Browse by category</h2>
          <p className="mt-1 text-sm text-muted">Jump into the events list filtered by category.</p>
        </div>
        <CategoryGrid categories={categories} />
      </section>
    </main>
  );
}
