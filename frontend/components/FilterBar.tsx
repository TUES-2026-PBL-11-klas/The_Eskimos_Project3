"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";

import type { Category, Venue } from "@/lib/api/types";

// Horizontal filter bar shown ABOVE the events grid. Filters are date-from,
// category and city only (no price, no end date). State lives in the URL search
// params (no store); changing any control resets to page 1.
export default function FilterBar({
  categories,
  cities,
  venues,
}: {
  categories: Category[];
  cities: string[];
  venues: Venue[];
}) {
  const router = useRouter();
  const pathname = usePathname();
  const sp = useSearchParams();

  const update = (key: string, value: string) => {
    const params = new URLSearchParams(sp.toString());
    if (value) params.set(key, value);
    else params.delete(key);
    params.delete("page");
    const qs = params.toString();
    router.push(qs ? `${pathname}?${qs}` : pathname);
  };

  const category = sp.get("category") ?? "";
  const city = sp.get("city") ?? "";
  const venueId = sp.get("venue_id") ?? "";
  const dateFrom = sp.get("date_from") ?? "";
  const hasFilters = Boolean(category || city || venueId || dateFrom);

  const labelCls = "mb-1.5 block text-xs font-semibold uppercase tracking-wide text-muted";
  const fieldCls =
    "w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-foreground focus:border-accent focus:outline-none";

  return (
    <div className="rounded-2xl border border-border bg-surface/60 p-4">
      <div className="flex flex-wrap items-end gap-4">
        <div className="min-w-[160px] flex-1">
          <label htmlFor="f-category" className={labelCls}>
            Category
          </label>
          <select
            id="f-category"
            className={fieldCls}
            value={category}
            onChange={(e) => update("category", e.target.value)}
          >
            <option value="">All categories</option>
            {categories.map((c) => (
              <option key={c.slug} value={c.slug}>
                {c.name}
              </option>
            ))}
          </select>
        </div>

        <div className="min-w-[160px] flex-1">
          <label htmlFor="f-city" className={labelCls}>
            City
          </label>
          <select
            id="f-city"
            className={fieldCls}
            value={city}
            onChange={(e) => update("city", e.target.value)}
          >
            <option value="">All cities</option>
            {cities.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>

        <div className="min-w-[160px] flex-1">
          <label htmlFor="f-venue" className={labelCls}>
            Venue
          </label>
          <select
            id="f-venue"
            className={fieldCls}
            value={venueId}
            onChange={(e) => update("venue_id", e.target.value)}
          >
            <option value="">All venues</option>
            {venues.map((v) => (
              <option key={v.id} value={v.id}>
                {v.name}
              </option>
            ))}
          </select>
        </div>

        <div className="min-w-[160px] flex-1">
          <label htmlFor="f-from" className={labelCls}>
            From date
          </label>
          <input
            id="f-from"
            type="date"
            className={fieldCls}
            value={dateFrom}
            onChange={(e) => update("date_from", e.target.value)}
          />
        </div>

        {hasFilters && (
          <button
            onClick={() => router.push(pathname)}
            className="rounded-lg border border-border bg-surface px-4 py-2 text-sm font-medium text-muted transition hover:border-accent hover:text-foreground"
          >
            Clear all
          </button>
        )}
      </div>
    </div>
  );
}
