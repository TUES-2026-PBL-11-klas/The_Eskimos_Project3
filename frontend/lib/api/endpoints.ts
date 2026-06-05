// Centralized, typed endpoint functions — the ONLY data entry point for the UI.
//
// Each function keeps one signature with two branches: the in-memory mock (while
// EVENTHUB_USE_MOCK is on) and a live `serverFetch` to the API mapped onto the UI
// view models. Public reads run in Server Components, so no bearer is attached.

import { serverFetch } from "./client";
import { USE_MOCK } from "./config";
import {
  type ApiCategoryWithCount,
  type ApiEvent,
  type ApiEventPage,
  type ApiStats,
  type ApiVenue,
  toCategory,
  toEventDetail,
  toEventSummary,
  toPaginated,
  toVenue,
} from "./mappers";
import { CATEGORIES, DESCRIPTIONS, EVENTS, VENUES } from "./mock";
import {
  ApiError,
  type Category,
  type EventDetail,
  type EventFilters,
  type EventSummary,
  type Paginated,
  type Stats,
  type Venue,
} from "./types";

const DEFAULT_SIZE = 9;

// Public event reads are cacheable; mirror the API's max-age=300.
const CACHE: RequestInit = { next: { revalidate: 300 } };

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
    if (f.venue_id && e.venue?.id !== f.venue_id) return false;
    if (f.date_from && day < f.date_from.slice(0, 10)) return false;
    if (f.date_to && day > f.date_to.slice(0, 10)) return false;
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
  const page = await serverFetch<ApiEventPage>("/events", {
    query: {
      date_from: filters.date_from,
      date_to: filters.date_to,
      category: filters.category,
      city: filters.city,
      venue_id: filters.venue_id,
      q: filters.q,
      page: filters.page ?? 1,
      size: filters.size ?? DEFAULT_SIZE,
    },
    init: CACHE,
  });
  return toPaginated(page);
}

/** GET /events/{id}. Throws ApiError(404) for an unknown id. */
export async function getEvent(id: string): Promise<EventDetail> {
  if (USE_MOCK) {
    const e = EVENTS.find((x) => x.id === id);
    if (!e) throw new ApiError(404, "Event not found");
    return { ...e, description: DESCRIPTIONS[e.id] ?? null };
  }
  const event = await serverFetch<ApiEvent>(`/events/${id}`, { init: CACHE });
  return toEventDetail(event);
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
  const events = await serverFetch<ApiEvent[]>("/events/upcoming", {
    query: { limit },
    init: CACHE,
  });
  return events.map(toEventSummary);
}

/** GET /categories — categories with event counts. */
export async function getCategories(): Promise<Category[]> {
  if (USE_MOCK) return [...CATEGORIES];
  const cats = await serverFetch<ApiCategoryWithCount[]>("/categories", { init: CACHE });
  return cats.map(toCategory);
}

/** GET /venues. */
export async function getVenues(): Promise<Venue[]> {
  if (USE_MOCK) return [...VENUES].sort((a, b) => a.name.localeCompare(b.name));
  const venues = await serverFetch<ApiVenue[]>("/venues", { init: CACHE });
  return venues.map(toVenue);
}

/** GET /search — full-text over title. */
export async function search(q: string): Promise<EventSummary[]> {
  if (USE_MOCK) {
    return applyFilters([...EVENTS], { q }).sort((a, b) => a.start_at.localeCompare(b.start_at));
  }
  if (q.trim() === "") return [];
  const events = await serverFetch<ApiEvent[]>("/search", { query: { q }, init: CACHE });
  return events.map(toEventSummary);
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
  // The API stats payload has no "upcoming" count; derive it from a 1-row page total.
  const [stats, upcomingPage] = await Promise.all([
    serverFetch<ApiStats>("/stats", { init: CACHE }),
    serverFetch<ApiEventPage>("/events", {
      query: { date_from: new Date().toISOString(), size: 1 },
      init: CACHE,
    }),
  ]);
  return {
    total_events: stats.total_events,
    upcoming_events: upcomingPage.total,
    total_categories: stats.total_categories,
    total_venues: stats.total_venues,
  };
}

/** Distinct cities across venues — for the filter dropdown. */
export async function getCities(): Promise<string[]> {
  const venues = USE_MOCK ? VENUES : await getVenues();
  const cities = new Set<string>();
  for (const v of venues) if (v.city) cities.add(v.city);
  return [...cities].sort();
}
