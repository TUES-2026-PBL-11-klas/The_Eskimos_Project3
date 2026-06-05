import type { Metadata } from "next";

import VenueList from "@/components/VenueList";
import { getVenues } from "@/lib/api/endpoints";

export const metadata: Metadata = { title: "Venues" };

// Render per request so the data source (mock vs live API) is honoured at runtime
// rather than baked in at build time.
export const dynamic = "force-dynamic";

export default async function VenuesPage() {
  const venues = await getVenues();

  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-foreground">Venues</h1>
        <p className="mt-1 text-sm text-muted">
          {venues.length} venues hosting events across the country.
        </p>
      </header>
      <VenueList venues={venues} />
    </main>
  );
}
