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
  date_to?: string;
  category?: string;
  city?: string;
  venue_id?: string;
  q?: string;
  page?: number;
  size?: number;
}

// ---------------------------------------------------------------------------
// Auth & per-user types (used by later phases; visuals only for now).
// ---------------------------------------------------------------------------

// Preferences mirror the `user_preferences` table exactly: only a default reminder
// lead time and a timezone (no category/city arrays — those columns don't exist).
export interface UserPreferences {
  default_lead_hours: number;
  timezone: string;
}

export interface Me {
  email: string;
  display_name: string;
  preferences: UserPreferences;
}

/**
 * A saved event as the UI consumes it. `id` is the originating EVENT id (so
 * `/events/[id]` links and the save-toggle match by it); `saved_id` is the
 * `/me/saved` record id used to unsave or attach a reminder.
 */
export interface SavedEvent extends EventSummary {
  saved_id: string;
  saved_at: string;
}

// The API only persists these two states (no "sent").
export type ReminderStatus = "pending" | "cancelled";

export interface Reminder {
  id: string;
  /** UI event id, resolved by joining the API reminder's saved_event_id → saved list. */
  event_id: string;
  event_title: string;
  remind_at: string;
  start_at: string;
  status: ReminderStatus;
}

export interface SessionInfo {
  id: string;
  user_agent: string;
  /** Not exposed by the API; present only in the mock. */
  ip?: string;
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
