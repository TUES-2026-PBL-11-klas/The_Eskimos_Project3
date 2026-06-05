// Client-side calls to the Next BFF route handlers (relative URLs). Used by the
// auth/user store when running against the live API. The browser never calls the
// API or touches the session token directly (D3) — every call here hits /api/*.

import {
  type ApiMe,
  type ApiReminder,
  type ApiSavedEvent,
  type ApiSession,
  toMe,
  toReminder,
  toSavedEvent,
  toSessionInfo,
} from "./mappers";
import type { Me, Reminder, SavedEvent, SessionInfo } from "./types";

export interface MutationResult {
  ok: boolean;
  status?: number;
  error?: string;
}

async function errorOf(res: Response): Promise<string | undefined> {
  const body = await res.json().catch(() => ({}));
  return body.error ?? body.detail;
}

// ── Auth ─────────────────────────────────────────────────────────────────────

export async function apiLogin(email: string, password: string): Promise<MutationResult> {
  const res = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  return res.ok ? { ok: true } : { ok: false, status: res.status, error: await errorOf(res) };
}

export async function apiRegister(
  email: string,
  password: string,
  display_name: string,
): Promise<MutationResult> {
  const res = await fetch("/api/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, display_name }),
  });
  return res.ok ? { ok: true } : { ok: false, status: res.status, error: await errorOf(res) };
}

export async function apiLogout(): Promise<void> {
  await fetch("/api/auth/logout", { method: "POST" });
}

// ── Reads ────────────────────────────────────────────────────────────────────

/** Returns the profile, or null when the session is missing/expired (401). */
export async function fetchMe(): Promise<Me | null> {
  const res = await fetch("/api/me");
  if (res.status === 401) return null;
  if (!res.ok) return null;
  return toMe((await res.json()) as ApiMe);
}

export async function fetchSaved(): Promise<SavedEvent[]> {
  const res = await fetch("/api/me/saved");
  if (!res.ok) return [];
  return ((await res.json()) as ApiSavedEvent[]).map(toSavedEvent);
}

function indexBySavedId(saved: SavedEvent[]): Map<string, SavedEvent> {
  return new Map(saved.map((s) => [s.saved_id, s]));
}

export async function fetchReminders(saved: SavedEvent[]): Promise<Reminder[]> {
  const res = await fetch("/api/me/reminders");
  if (!res.ok) return [];
  const byId = indexBySavedId(saved);
  return ((await res.json()) as ApiReminder[])
    .map((r) => toReminder(r, byId))
    .filter((r): r is Reminder => r !== null);
}

export async function fetchDueReminders(saved: SavedEvent[]): Promise<Reminder[]> {
  const res = await fetch("/api/me/reminders/due");
  if (!res.ok) return [];
  const byId = indexBySavedId(saved);
  return ((await res.json()) as ApiReminder[])
    .map((r) => toReminder(r, byId))
    .filter((r): r is Reminder => r !== null);
}

export async function fetchSessions(): Promise<SessionInfo[]> {
  const res = await fetch("/api/auth/sessions");
  if (!res.ok) return [];
  return ((await res.json()) as ApiSession[]).map((s) => toSessionInfo(s, null));
}

// ── Mutations ────────────────────────────────────────────────────────────────

export async function saveEvent(eventId: string): Promise<MutationResult> {
  const res = await fetch("/api/me/saved", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ event_id: eventId }),
  });
  return res.ok ? { ok: true } : { ok: false, status: res.status, error: await errorOf(res) };
}

export async function unsaveEvent(savedId: string): Promise<MutationResult> {
  const res = await fetch(`/api/me/saved/${savedId}`, { method: "DELETE" });
  return res.ok ? { ok: true } : { ok: false, status: res.status, error: await errorOf(res) };
}

export async function createReminder(
  savedId: string,
  body: { lead_hours?: number; remind_at?: string },
): Promise<MutationResult> {
  const res = await fetch(`/api/me/saved/${savedId}/reminder`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return res.ok ? { ok: true } : { ok: false, status: res.status, error: await errorOf(res) };
}

export async function cancelReminderApi(reminderId: string): Promise<MutationResult> {
  const res = await fetch(`/api/me/reminders/${reminderId}`, { method: "DELETE" });
  return res.ok ? { ok: true } : { ok: false, status: res.status, error: await errorOf(res) };
}

export async function revokeSessionApi(sessionId: string): Promise<MutationResult> {
  const res = await fetch(`/api/auth/sessions/${sessionId}`, { method: "DELETE" });
  return res.ok ? { ok: true } : { ok: false, status: res.status, error: await errorOf(res) };
}

export async function patchMe(body: {
  display_name?: string;
  default_lead_hours?: number;
  timezone?: string;
}): Promise<Me | null> {
  const res = await fetch("/api/me", {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) return null;
  return toMe((await res.json()) as ApiMe);
}
