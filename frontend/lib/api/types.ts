// EventHub API types.
//
// These are HAND-WRITTEN to mirror the documented API contract (plan Section 1)
// because the API service is not reachable right now to generate from
// `/openapi.json`. When the API is up, run the `gen-api` task to produce
// `lib/api/schema.d.ts` and migrate these to the generated types.
//
// Per decision D2: NO price and NO end time anywhere. Events expose only
// title, start_at, venue, category and a source link.

/** A venue as embedded on an event, and as listed by GET /venues. */
export interface Venue {
  id: string;
  name: string;
  city: string | null;
}

/** Event shape for cards / lists (GET /events items, /events/upcoming, /search). */
export interface EventSummary {
  id: string;
  title: string;
  /** ISO-8601 start datetime. The ONLY time field (no end_at by D2). */
  start_at: string;
  category: string | null;
  venue: Venue | null;
}

/** Full event detail (GET /events/{id}). */
export interface EventDetail extends EventSummary {
  description: string | null;
}

/** Paginated envelope returned by GET /events. */
export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

/** GET /categories — categories with their event counts. */
export interface Category {
  name: string;
  slug: string;
  count: number;
}

/** GET /stats — aggregate counts for the landing page. */
export interface Stats {
  total_events: number;
  upcoming_events: number;
  total_categories: number;
  total_venues: number;
}

/** Query params accepted by GET /events. */
export interface EventFilters {
  date_from?: string;
  category?: string;
  city?: string;
  q?: string;
  page?: number;
  size?: number;
}

// ---------------------------------------------------------------------------
// Auth & per-user types (used by later phases; visuals only for now).
// ---------------------------------------------------------------------------

export interface UserPreferences {
  categories: string[];
  cities: string[];
  default_lead_hours: number;
}

export interface Me {
  email: string;
  display_name: string;
  preferences: UserPreferences;
}

export interface SavedEvent extends EventSummary {
  saved_at: string;
}

export type ReminderStatus = "pending" | "sent" | "cancelled";

export interface Reminder {
  id: string;
  event_id: string;
  event_title: string;
  remind_at: string;
  start_at: string;
  status: ReminderStatus;
}

export interface SessionInfo {
  id: string;
  user_agent: string;
  ip: string;
  created_at: string;
  current: boolean;
}

/** Error carrying the HTTP status so callers can branch on 401/404/409. */
export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public body?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}
