// Centralized, typed endpoint functions — the ONLY data entry point for the UI.
//
// While USE_MOCK is on (the API is unreachable) these resolve against the
// in-memory mock with real filtering / pagination / search so the visuals are
// genuinely interactive. When the API is up, replace each mock branch with a
// `serverFetch(...)` / `browserFetch(...)` call — signatures stay identical, so
// no page or component changes.

import { USE_MOCK } from "./config";
import { CATEGORIES, DESCRIPTIONS, EVENTS, VENUES } from "./mock";
import type {
  Category,
  EventDetail,
  EventFilters,
  EventSummary,
  Paginated,
  Stats,
  Venue,
} from "./types";
import { ApiError } from "./types";

const DEFAULT_SIZE = 9;

function paginate<T>(items: T[], page: number, size: number): Paginated<T> {
  const total = items.length;
  const pages = Math.max(1, Math.ceil(total / size));
  const safePage = Math.min(Math.max(1, page), pages);
  const start = (safePage - 1) * size;
  return { items: items.slice(start, start + size), total, page: safePage, size, pages };
}

function applyFilters(list: EventSummary[], f: EventFilters): EventSummary[] {
  const q = f.q?.trim().toLowerCase();
  return list.filter((e) => {
    const day = e.start_at.slice(0, 10); // yyyy-mm-dd, for inclusive date bounds
    if (f.category && e.category !== f.category) return false;
    if (f.city && e.venue?.city !== f.city) return false;
    if (f.date_from && day < f.date_from.slice(0, 10)) return false;
    if (q) {
      const hay = `${e.title} ${DESCRIPTIONS[e.id] ?? ""}`.toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  });
}

// ---------------------------------------------------------------------------
// Public, read-only endpoints
// ---------------------------------------------------------------------------

/** GET /events — all events, filtered + paginated. */
export async function getEvents(filters: EventFilters = {}): Promise<Paginated<EventSummary>> {
  if (USE_MOCK) {
    const filtered = applyFilters([...EVENTS], filters).sort((a, b) =>
      a.start_at.localeCompare(b.start_at),
    );
    return paginate(filtered, filters.page ?? 1, filters.size ?? DEFAULT_SIZE);
  }
  throw new ApiError(503, "Live API not wired yet");
}

/** GET /events/{id}. Throws ApiError(404) for an unknown id. */
export async function getEvent(id: string): Promise<EventDetail> {
  if (USE_MOCK) {
    const e = EVENTS.find((x) => x.id === id);
    if (!e) throw new ApiError(404, "Event not found");
    return { ...e, description: DESCRIPTIONS[e.id] ?? null };
  }
  throw new ApiError(503, "Live API not wired yet");
}

/** GET /events/upcoming — nearest events by time (start_at >= now ASC). */
export async function getUpcoming(limit = 6): Promise<EventSummary[]> {
  if (USE_MOCK) {
    const now = new Date().toISOString();
    return [...EVENTS]
      .filter((e) => e.start_at >= now)
      .sort((a, b) => a.start_at.localeCompare(b.start_at))
      .slice(0, limit);
  }
  throw new ApiError(503, "Live API not wired yet");
}

/** GET /categories — categories with event counts. */
export async function getCategories(): Promise<Category[]> {
  if (USE_MOCK) return [...CATEGORIES];
  throw new ApiError(503, "Live API not wired yet");
}

/** GET /venues. */
export async function getVenues(): Promise<Venue[]> {
  if (USE_MOCK) return [...VENUES].sort((a, b) => a.name.localeCompare(b.name));
  throw new ApiError(503, "Live API not wired yet");
}

/** GET /search — full-text over title/description. */
export async function search(q: string): Promise<EventSummary[]> {
  if (USE_MOCK) {
    return applyFilters([...EVENTS], { q }).sort((a, b) => a.start_at.localeCompare(b.start_at));
  }
  throw new ApiError(503, "Live API not wired yet");
}

/** GET /stats — aggregate counts for the landing page. */
export async function getStats(): Promise<Stats> {
  if (USE_MOCK) {
    const now = new Date().toISOString();
    return {
      total_events: EVENTS.length,
      upcoming_events: EVENTS.filter((e) => e.start_at >= now).length,
      total_categories: CATEGORIES.length,
      total_venues: VENUES.length,
    };
  }
  throw new ApiError(503, "Live API not wired yet");
}

/** Distinct cities across venues — for the filter dropdown. */
export async function getCities(): Promise<string[]> {
  const cities = new Set<string>();
  for (const v of VENUES) if (v.city) cities.add(v.city);
  return [...cities].sort();
}
