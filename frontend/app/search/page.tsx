import type { Metadata } from "next";

import EventList from "@/components/EventList";
import SearchBar from "@/components/SearchBar";
import { EmptyState } from "@/components/states";
import { search } from "@/lib/api/endpoints";

export const metadata: Metadata = { title: "Search" };

type SearchParams = Promise<Record<string, string | string[] | undefined>>;

export default async function SearchPage({ searchParams }: { searchParams: SearchParams }) {
  const sp = await searchParams;
  const raw = sp.q;
  const q = (Array.isArray(raw) ? raw[0] : raw)?.trim() ?? "";

  const results = q ? await search(q) : [];

  return (
    <main className="mx-auto max-w-4xl px-6 py-10">
      <h1 className="text-3xl font-bold text-foreground">Search events</h1>

      <div className="mt-5">
        <SearchBar defaultValue={q} autoNavigate autoFocus placeholder="Search by title or description…" />
      </div>

      <div className="mt-8">
        {!q ? (
          <EmptyState
            icon="🔎"
            title="Start typing to search"
            message="Find events by title or description — try “jazz”, “workshop” or “festival”."
          />
        ) : (
          <>
            <p className="mb-5 text-sm text-muted">
              {results.length} {results.length === 1 ? "result" : "results"} for “{q}”
            </p>
            <EventList
              events={results}
              emptyTitle="No matches"
              emptyMessage={`Nothing found for “${q}”. Try a different term.`}
            />
          </>
        )}
      </div>
    </main>
  );
}
