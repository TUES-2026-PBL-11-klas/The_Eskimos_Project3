import Link from "next/link";

import type { Venue } from "@/lib/api/types";

// Venues grouped by city. Each venue links into the all-events list filtered by
// its city (feeding the same `city` filter the sidebar uses).
export default function VenueList({ venues }: { venues: Venue[] }) {
  const byCity = new Map<string, Venue[]>();
  for (const v of venues) {
    const city = v.city ?? "Other";
    if (!byCity.has(city)) byCity.set(city, []);
    byCity.get(city)!.push(v);
  }
  const cities = [...byCity.keys()].sort();

  return (
    <div className="space-y-10">
      {cities.map((city) => (
        <section key={city}>
          <div className="mb-4 flex items-center gap-3">
            <h2 className="text-xl font-semibold text-foreground">{city}</h2>
            <span className="rounded-full bg-surface-2 px-2.5 py-0.5 text-xs text-muted">
              {byCity.get(city)!.length} venues
            </span>
            <Link
              href={`/events?city=${encodeURIComponent(city)}`}
              className="ml-auto text-sm font-medium text-accent hover:text-accent-hover"
            >
              Events in {city} →
            </Link>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {byCity.get(city)!.map((v) => (
              <Link
                key={v.id}
                href={`/events?venue_id=${v.id}`}
                className="group flex items-center gap-3 rounded-2xl border border-border bg-surface p-4 transition hover:border-accent/60 hover:bg-surface-2"
              >
                <span className="grid h-10 w-10 place-items-center rounded-xl bg-surface-2 text-lg">
                  📍
                </span>
                <div>
                  <p className="font-medium text-foreground group-hover:text-accent-hover">
                    {v.name}
                  </p>
                  <p className="text-sm text-muted">{v.city}</p>
                </div>
              </Link>
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}
