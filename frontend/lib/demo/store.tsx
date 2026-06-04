"use client";

// CLIENT-SIDE DEMO STORE — stands in for the authenticated server state while the
// API is offline (visuals only). It simulates: a logged-in user, their saved
// events (snapshots), reminders and active sessions, persisted to localStorage so
// the experience survives reloads.
//
// This is NOT the real auth model. Per D3/D5 the production app holds an opaque
// session token in an httpOnly cookie and reads this data from the API via route
// handlers — none of which can run with the API down. Replace this provider with
// the real BFF-backed data in the auth pass.

import { createContext, useContext, useEffect, useMemo, useState } from "react";

import { EVENTS } from "@/lib/api/mock";
import type { EventSummary, Me, Reminder, SavedEvent, SessionInfo } from "@/lib/api/types";

const STORAGE_KEY = "eventhub_demo_v1";
const HOUR = 60 * 60 * 1000;
const DAY = 24 * HOUR;

const DEMO_USER: Me = {
  email: "demo@eventhub.bg",
  display_name: "Demo User",
  preferences: { categories: ["Music", "Tech"], cities: ["Sofia"], default_lead_hours: 24 },
};

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

// First-visit seed: a couple of saved events and one already-due reminder, so the
// calendar, reminders list and due-reminders popup all have something to show.
function seed(): { saved: SavedEvent[]; reminders: Reminder[] } {
  const now = Date.now();
  const upcoming = [...EVENTS]
    .filter((e) => new Date(e.start_at).getTime() > now)
    .sort((a, b) => a.start_at.localeCompare(b.start_at));
  const saved: SavedEvent[] = upcoming
    .slice(0, 3)
    .map((e) => ({ ...e, saved_at: new Date().toISOString() }));

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

interface DemoState extends Persisted {
  user: Me;
  hydrated: boolean;
}

interface DemoContextValue extends DemoState {
  login: () => void;
  logout: () => void;
  isSaved: (id: string) => boolean;
  toggleSave: (event: EventSummary) => void;
  unsave: (id: string) => void;
  reminderFor: (eventId: string) => Reminder | undefined;
  addReminder: (event: EventSummary) => { ok: boolean; error?: string };
  cancelReminder: (id: string) => void;
  dueReminders: () => Reminder[];
  revokeSession: (id: string) => void;
}

const DemoContext = createContext<DemoContextValue | null>(null);

export function DemoProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<DemoState>({
    loggedIn: true,
    saved: [],
    reminders: [],
    sessions: [],
    user: DEMO_USER,
    hydrated: false,
  });

  // Hydrate from localStorage after mount. setState-in-effect is intentional:
  // reading localStorage during render would cause an SSR/client mismatch, so we
  // render defaults first and reconcile (or seed) on mount.
  /* eslint-disable react-hooks/set-state-in-effect */
  useEffect(() => {
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
  }, []);
  /* eslint-enable react-hooks/set-state-in-effect */

  // Persist on change (once hydrated).
  useEffect(() => {
    if (!state.hydrated) return;
    const data: Persisted = {
      loggedIn: state.loggedIn,
      saved: state.saved,
      reminders: state.reminders,
      sessions: state.sessions,
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  }, [state]);

  const value = useMemo<DemoContextValue>(() => {
    const isSaved = (id: string) => state.saved.some((e) => e.id === id);

    return {
      ...state,

      login: () => setState((s) => ({ ...s, loggedIn: true })),
      logout: () => setState((s) => ({ ...s, loggedIn: false })),

      isSaved,

      toggleSave: (event) =>
        setState((s) => {
          if (s.saved.some((e) => e.id === event.id)) {
            return {
              ...s,
              saved: s.saved.filter((e) => e.id !== event.id),
              // Unsaving cascades its reminders (mirrors the API behaviour).
              reminders: s.reminders.filter((r) => r.event_id !== event.id),
            };
          }
          const snapshot: SavedEvent = { ...event, saved_at: new Date().toISOString() };
          return { ...s, saved: [...s.saved, snapshot] };
        }),

      unsave: (id) =>
        setState((s) => ({
          ...s,
          saved: s.saved.filter((e) => e.id !== id),
          reminders: s.reminders.filter((r) => r.event_id !== id),
        })),

      reminderFor: (eventId) =>
        state.reminders.find((r) => r.event_id === eventId && r.status === "pending"),

      addReminder: (event) => {
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

      cancelReminder: (id) =>
        setState((s) => ({
          ...s,
          reminders: s.reminders.map((r) => (r.id === id ? { ...r, status: "cancelled" } : r)),
        })),

      dueReminders: () =>
        state.reminders.filter(
          (r) => r.status === "pending" && new Date(r.remind_at).getTime() <= Date.now(),
        ),

      revokeSession: (id) =>
        setState((s) => ({ ...s, sessions: s.sessions.filter((sess) => sess.id !== id) })),
    };
  }, [state]);

  return <DemoContext.Provider value={value}>{children}</DemoContext.Provider>;
}

export function useDemo(): DemoContextValue {
  const ctx = useContext(DemoContext);
  if (!ctx) throw new Error("useDemo must be used within DemoProvider");
  return ctx;
}
