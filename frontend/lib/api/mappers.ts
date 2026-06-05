// Maps the raw API (Pydantic) shapes onto the UI view models in types.ts.
// Centralising this keeps pages/components free of the int→string coercion and
// nested→flat reshaping the API requires. The raw shapes below are hand-written
// to match the live schemas (api/src/api/schemas/*); once `gen-api` has produced
// schema.d.ts they can be swapped for the generated types.

import type {
  Category,
  EventDetail,
  EventSummary,
  Me,
  Paginated,
  Reminder,
  SavedEvent,
  SessionInfo,
  Venue,
} from "./types";

// ── Raw API shapes ───────────────────────────────────────────────────────────

export interface ApiSource {
  id: number;
  name: string;
  type: string;
}

export interface ApiVenue {
  id: number;
  name: string;
  city: string | null;
}

export interface ApiCategory {
  id: number;
  name: string;
  slug: string;
}

export interface ApiEvent {
  id: number;
  title: string;
  description: string | null;
  start_at: string;
  url: string;
  source: ApiSource | null;
  venue: ApiVenue | null;
  category: ApiCategory | null;
  created_at: string;
  updated_at: string;
}

export interface ApiEventPage {
  items: ApiEvent[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface ApiCategoryWithCount {
  category: ApiCategory;
  count: number;
}

export interface ApiStats {
  total_events: number;
  total_venues: number;
  total_categories: number;
  total_sources: number;
}

export interface ApiSavedEvent {
  id: number;
  source: string;
  external_id: string;
  event_id: number | null;
  title: string;
  start_at: string;
  venue_name: string | null;
  city: string | null;
  category: string | null;
  url: string;
  saved_at: string;
}

export interface ApiReminder {
  id: number;
  saved_event_id: number;
  remind_at: string;
  status: "pending" | "cancelled";
  created_at: string;
}

export interface ApiSession {
  id: number;
  created_at: string;
  expires_at: string;
  user_agent: string | null;
}

export interface ApiMe {
  id: number;
  email: string;
  display_name: string | null;
  created_at: string;
  preferences: { default_lead_hours: number; timezone: string };
}

// ── Mappers ──────────────────────────────────────────────────────────────────

function toVenueEmbedded(v: ApiVenue | null): Venue | null {
  return v ? { id: String(v.id), name: v.name, city: v.city } : null;
}

export function toEventSummary(e: ApiEvent): EventSummary {
  return {
    id: String(e.id),
    title: e.title,
    start_at: e.start_at,
    category: e.category?.name ?? null,
    venue: toVenueEmbedded(e.venue),
  };
}

export function toEventDetail(e: ApiEvent): EventDetail {
  return { ...toEventSummary(e), description: e.description };
}

export function toPaginated(p: ApiEventPage): Paginated<EventSummary> {
  return {
    items: p.items.map(toEventSummary),
    total: p.total,
    page: p.page,
    size: p.size,
    pages: p.pages,
  };
}

export function toCategory(c: ApiCategoryWithCount): Category {
  return { name: c.category.name, slug: c.category.slug, count: c.count };
}

export function toVenue(v: ApiVenue): Venue {
  return { id: String(v.id), name: v.name, city: v.city };
}

export function toSavedEvent(s: ApiSavedEvent): SavedEvent {
  return {
    // `id` is the originating event id so /events/[id] links & the save-toggle work.
    // Fall back to the saved-record id for legacy rows that predate event_id.
    id: String(s.event_id ?? s.id),
    saved_id: String(s.id),
    title: s.title,
    start_at: s.start_at,
    category: s.category,
    venue: s.venue_name ? { id: "", name: s.venue_name, city: s.city } : null,
    saved_at: s.saved_at,
  };
}

/**
 * Build the UI reminder by joining the API reminder (which has no event context)
 * with the saved-events list via saved_event_id. Reminders whose saved event is
 * gone are dropped.
 */
export function toReminder(r: ApiReminder, savedById: Map<string, SavedEvent>): Reminder | null {
  const saved = savedById.get(String(r.saved_event_id));
  if (!saved) return null;
  return {
    id: String(r.id),
    event_id: saved.id,
    event_title: saved.title,
    remind_at: r.remind_at,
    start_at: saved.start_at,
    status: r.status,
  };
}

export function toSessionInfo(s: ApiSession, currentId: number | null): SessionInfo {
  return {
    id: String(s.id),
    user_agent: s.user_agent ?? "Unknown device",
    created_at: s.created_at,
    current: currentId !== null && s.id === currentId,
  };
}

export function toMe(m: ApiMe): Me {
  return {
    email: m.email,
    display_name: m.display_name ?? m.email,
    preferences: {
      default_lead_hours: m.preferences.default_lead_hours,
      timezone: m.preferences.timezone,
    },
  };
}
