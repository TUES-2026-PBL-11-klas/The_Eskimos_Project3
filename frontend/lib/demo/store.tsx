"use client";

// Authenticated client state for EventHub. One provider, two backends:
//
//   • useMock=true  — an in-memory demo (localStorage-backed) so the whole app
//     runs offline: a logged-in user, saved events, reminders and sessions.
//   • useMock=false — the live API via the Next route-handler BFF. The opaque
//     session token lives in an httpOnly cookie (D3); this store only ever calls
//     /api/* and never sees the token. Mutations re-read server state so the UI
//     reflects the source of truth.
//
// The context interface is identical for both, so pages/components don't care
// which backend is active. Mutating methods are async in both (the mock resolves
// immediately).

import { createContext, useContext, useEffect, useMemo, useState } from "react";

import {
  apiLogin,
  apiLogout,
  apiRegister,
  cancelReminderApi,
  createReminder,
  fetchDueReminders,
  fetchMe,
  fetchReminders,
  fetchSaved,
  fetchSessions,
  patchMe,
  revokeSessionApi,
  saveEvent,
  unsaveEvent,
} from "@/lib/api/me-client";
import { EVENTS } from "@/lib/api/mock";
import type { EventSummary, Me, Reminder, SavedEvent, SessionInfo } from "@/lib/api/types";
import { mockLogin, mockRegister } from "@/lib/auth/mock-auth";
import { ApiError } from "@/lib/api/types";

const STORAGE_KEY = "eventhub_demo_v1";
const HOUR = 60 * 60 * 1000;
const DAY = 24 * HOUR;

const EMPTY_USER: Me = {
  email: "",
  display_name: "",
  preferences: { default_lead_hours: 24, timezone: "Europe/Sofia" },
};

const DEMO_USER: Me = {
  email: "demo@eventhub.bg",
  display_name: "Demo User",
  preferences: { default_lead_hours: 24, timezone: "Europe/Sofia" },
};

export interface AuthResult {
  ok: boolean;
  status?: number;
  error?: string;
}

function defaultSessions(): SessionInfo[] {
  const now = Date.now();
  return [
    {
      id: "s_current",
      user_agent: "Chrome 124 · Windows 11",
      ip: "78.90.12.4",
      created_at: new Date(now - 2 * DAY).toISOString(),
      current: true,
    },
    {
      id: "s_phone",
      user_agent: "Safari · iPhone",
      ip: "78.90.12.9",
      created_at: new Date(now - 5 * DAY).toISOString(),
      current: false,
    },
    {
      id: "s_mac",
      user_agent: "Firefox · macOS",
      ip: "85.11.3.2",
      created_at: new Date(now - 20 * DAY).toISOString(),
      current: false,
    },
  ];
}

// First-visit seed (mock only): a couple of saved events and one already-due
// reminder so the calendar, reminders list and due-reminders popup have content.
function seed(): { saved: SavedEvent[]; reminders: Reminder[] } {
  const now = Date.now();
  const upcoming = [...EVENTS]
    .filter((e) => new Date(e.start_at).getTime() > now)
    .sort((a, b) => a.start_at.localeCompare(b.start_at));
  const saved: SavedEvent[] = upcoming
    .slice(0, 3)
    .map((e) => ({ ...e, saved_id: e.id, saved_at: new Date().toISOString() }));

  const reminders: Reminder[] = [];
  if (saved[0]) {
    reminders.push({
      id: "r_seed_due",
      event_id: saved[0].id,
      event_title: saved[0].title,
      remind_at: new Date(now - 2 * HOUR).toISOString(), // already due
      start_at: saved[0].start_at,
      status: "pending",
    });
  }
  return { saved, reminders };
}

interface Persisted {
  loggedIn: boolean;
  saved: SavedEvent[];
  reminders: Reminder[];
  sessions: SessionInfo[];
}

interface DemoState {
  loggedIn: boolean;
  saved: SavedEvent[];
  reminders: Reminder[];
  /** Server-computed due reminders (live); for the mock this stays empty and
   *  dueReminders() derives them from `reminders`. */
  due: Reminder[];
  sessions: SessionInfo[];
  user: Me;
  hydrated: boolean;
}

interface DemoContextValue extends DemoState {
  login: (email: string, password: string) => Promise<AuthResult>;
  register: (email: string, password: string, displayName: string) => Promise<AuthResult>;
  logout: () => Promise<void>;
  isSaved: (eventId: string) => boolean;
  toggleSave: (event: EventSummary) => Promise<void>;
  unsave: (eventId: string) => Promise<void>;
  reminderFor: (eventId: string) => Reminder | undefined;
  addReminder: (event: EventSummary) => Promise<AuthResult>;
  cancelReminder: (id: string) => Promise<void>;
  dueReminders: () => Reminder[];
  revokeSession: (id: string) => Promise<void>;
  updatePreferences: (leadHours: number) => Promise<void>;
}

const DemoContext = createContext<DemoContextValue | null>(null);

export function DemoProvider({
  children,
  useMock = true,
}: {
  children: React.ReactNode;
  useMock?: boolean;
}) {
  const [state, setState] = useState<DemoState>({
    // Mock starts logged-in (demo account); live starts logged-out until the
    // session cookie is confirmed by fetchMe().
    loggedIn: useMock,
    saved: [],
    reminders: [],
    due: [],
    sessions: [],
    user: useMock ? DEMO_USER : EMPTY_USER,
    hydrated: false,
  });

  // ── Hydration ───────────────────────────────────────────────────────────────
  /* eslint-disable react-hooks/set-state-in-effect */
  useEffect(() => {
    if (!useMock) {
      let active = true;
      (async () => {
        const data = await bootstrapLive();
        if (active) setState((s) => ({ ...s, ...data, hydrated: true }));
      })();
      return () => {
        active = false;
      };
    }

    // Mock: hydrate from localStorage (or seed first-visit data).
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed: Partial<Persisted> = JSON.parse(raw);
        setState((s) => ({
          ...s,
          loggedIn: parsed.loggedIn ?? true,
          saved: parsed.saved ?? [],
          reminders: parsed.reminders ?? [],
          sessions: parsed.sessions ?? defaultSessions(),
          hydrated: true,
        }));
      } else {
        const seeded = seed();
        setState((s) => ({
          ...s,
          saved: seeded.saved,
          reminders: seeded.reminders,
          sessions: defaultSessions(),
          hydrated: true,
        }));
      }
    } catch {
      setState((s) => ({ ...s, sessions: defaultSessions(), hydrated: true }));
    }
    return undefined;
  }, [useMock]);
  /* eslint-enable react-hooks/set-state-in-effect */

  // Persist mock state on change (once hydrated).
  useEffect(() => {
    if (!useMock || !state.hydrated) return;
    const data: Persisted = {
      loggedIn: state.loggedIn,
      saved: state.saved,
      reminders: state.reminders,
      sessions: state.sessions,
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  }, [useMock, state]);

  const value = useMemo<DemoContextValue>(() => {
    const isSaved = (eventId: string) => state.saved.some((e) => e.id === eventId);
    const savedFor = (eventId: string) => state.saved.find((e) => e.id === eventId);

    // Re-read saved events + reminders from the API after a mutation (live only).
    const reloadSaved = async () => {
      const saved = await fetchSaved();
      const [reminders, due] = await Promise.all([
        fetchReminders(saved),
        fetchDueReminders(saved),
      ]);
      setState((s) => ({ ...s, saved, reminders, due }));
    };

    // ── Mock implementations ──────────────────────────────────────────────────
    if (useMock) {
      return {
        ...state,
        isSaved,

        login: async (_email, password) => {
          try {
            await mockLogin({ email: _email, password });
            setState((s) => ({ ...s, loggedIn: true }));
            return { ok: true };
          } catch (err) {
            if (err instanceof ApiError) return { ok: false, status: err.status, error: err.message };
            return { ok: false, error: "Something went wrong." };
          }
        },

        register: async (email, password, displayName) => {
          try {
            await mockRegister({ email, password, display_name: displayName });
            setState((s) => ({ ...s, loggedIn: true }));
            return { ok: true };
          } catch (err) {
            if (err instanceof ApiError) return { ok: false, status: err.status, error: err.message };
            return { ok: false, error: "Something went wrong." };
          }
        },

        logout: async () => setState((s) => ({ ...s, loggedIn: false })),

        toggleSave: async (event) =>
          setState((s) => {
            if (s.saved.some((e) => e.id === event.id)) {
              return {
                ...s,
                saved: s.saved.filter((e) => e.id !== event.id),
                reminders: s.reminders.filter((r) => r.event_id !== event.id),
              };
            }
            const snapshot: SavedEvent = {
              ...event,
              saved_id: event.id,
              saved_at: new Date().toISOString(),
            };
            return { ...s, saved: [...s.saved, snapshot] };
          }),

        unsave: async (eventId) =>
          setState((s) => ({
            ...s,
            saved: s.saved.filter((e) => e.id !== eventId),
            reminders: s.reminders.filter((r) => r.event_id !== eventId),
          })),

        reminderFor: (eventId) =>
          state.reminders.find((r) => r.event_id === eventId && r.status === "pending"),

        addReminder: async (event) => {
          const lead = state.user.preferences.default_lead_hours;
          const remindAt = new Date(new Date(event.start_at).getTime() - lead * HOUR);
          if (remindAt.getTime() <= Date.now()) {
            return {
              ok: false,
              error: `This event is too soon — a reminder ${lead}h before has already passed.`,
            };
          }
          if (state.reminders.some((r) => r.event_id === event.id && r.status === "pending")) {
            return { ok: false, error: "You already have a reminder for this event." };
          }
          const reminder: Reminder = {
            id: crypto.randomUUID(),
            event_id: event.id,
            event_title: event.title,
            remind_at: remindAt.toISOString(),
            start_at: event.start_at,
            status: "pending",
          };
          setState((s) => ({ ...s, reminders: [...s.reminders, reminder] }));
          return { ok: true };
        },

        cancelReminder: async (id) =>
          setState((s) => ({
            ...s,
            reminders: s.reminders.map((r) =>
              r.id === id ? { ...r, status: "cancelled" } : r,
            ),
          })),

        dueReminders: () =>
          state.reminders.filter(
            (r) => r.status === "pending" && new Date(r.remind_at).getTime() <= Date.now(),
          ),

        revokeSession: async (id) =>
          setState((s) => ({ ...s, sessions: s.sessions.filter((sess) => sess.id !== id) })),

        updatePreferences: async (leadHours) =>
          setState((s) => ({
            ...s,
            user: {
              ...s.user,
              preferences: { ...s.user.preferences, default_lead_hours: leadHours },
            },
          })),
      };
    }

    // ── Live implementations (BFF) ──────────────────────────────────────────────
    return {
      ...state,
      isSaved,

      login: async (email, password) => {
        const result = await apiLogin(email, password);
        if (!result.ok) return result;
        const data = await bootstrapLive();
        setState((s) => ({ ...s, ...data, hydrated: true }));
        return { ok: true };
      },

      register: async (email, password, displayName) => {
        const result = await apiRegister(email, password, displayName);
        if (!result.ok) return result;
        const data = await bootstrapLive();
        setState((s) => ({ ...s, ...data, hydrated: true }));
        return { ok: true };
      },

      logout: async () => {
        await apiLogout();
        setState((s) => ({
          ...s,
          loggedIn: false,
          user: EMPTY_USER,
          saved: [],
          reminders: [],
          due: [],
          sessions: [],
        }));
      },

      toggleSave: async (event) => {
        const existing = savedFor(event.id);
        if (existing) await unsaveEvent(existing.saved_id);
        else await saveEvent(event.id);
        await reloadSaved();
      },

      unsave: async (eventId) => {
        const existing = savedFor(eventId);
        if (existing) await unsaveEvent(existing.saved_id);
        await reloadSaved();
      },

      reminderFor: (eventId) =>
        state.reminders.find((r) => r.event_id === eventId && r.status === "pending"),

      addReminder: async (event) => {
        const existing = savedFor(event.id);
        if (!existing) return { ok: false, error: "Save the event before setting a reminder." };
        const result = await createReminder(existing.saved_id, {});
        if (!result.ok) {
          return { ok: false, error: result.error ?? "Couldn't set a reminder." };
        }
        await reloadSaved();
        return { ok: true };
      },

      cancelReminder: async (id) => {
        await cancelReminderApi(id);
        await reloadSaved();
      },

      dueReminders: () => state.due,

      revokeSession: async (id) => {
        await revokeSessionApi(id);
        const sessions = await fetchSessions();
        setState((s) => ({ ...s, sessions }));
      },

      updatePreferences: async (leadHours) => {
        const me = await patchMe({ default_lead_hours: leadHours });
        if (me) setState((s) => ({ ...s, user: me }));
      },
    };
  }, [state, useMock]);

  return <DemoContext.Provider value={value}>{children}</DemoContext.Provider>;
}

/** Fetch the full authenticated state from the BFF (live mode). */
async function bootstrapLive(): Promise<Partial<DemoState>> {
  const user = await fetchMe();
  if (!user) {
    return { loggedIn: false, user: EMPTY_USER, saved: [], reminders: [], due: [], sessions: [] };
  }
  const saved = await fetchSaved();
  const [reminders, due, sessions] = await Promise.all([
    fetchReminders(saved),
    fetchDueReminders(saved),
    fetchSessions(),
  ]);
  return { loggedIn: true, user, saved, reminders, due, sessions };
}

export function useDemo(): DemoContextValue {
  const ctx = useContext(DemoContext);
  if (!ctx) throw new Error("useDemo must be used within DemoProvider");
  return ctx;
}
