"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import type { SavedEvent } from "@/lib/api/types";
import { categoryStyle } from "@/lib/categories";
import { formatTime } from "@/lib/format";

const WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

function ymd(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(
    d.getDate(),
  ).padStart(2, "0")}`;
}

// Month grid of saved events. A day is "marked" if it has >=1 saved event.
// Clicking a day lists that day's events. Mirrors /me/calendar (month=YYYY-MM).
export default function CalendarView({ events }: { events: SavedEvent[] }) {
  const today = new Date();
  const [cursor, setCursor] = useState(new Date(today.getFullYear(), today.getMonth(), 1));
  const [selected, setSelected] = useState<string | null>(null);

  // Bucket saved events by local date string.
  const byDay = useMemo(() => {
    const map = new Map<string, SavedEvent[]>();
    for (const e of events) {
      const key = ymd(new Date(e.start_at));
      if (!map.has(key)) map.set(key, []);
      map.get(key)!.push(e);
    }
    for (const list of map.values()) list.sort((a, b) => a.start_at.localeCompare(b.start_at));
    return map;
  }, [events]);

  const year = cursor.getFullYear();
  const month = cursor.getMonth();
  const firstDay = new Date(year, month, 1);
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  // Monday-start offset (getDay: Sun=0 → 6, Mon=1 → 0 …).
  const leadingBlanks = (firstDay.getDay() + 6) % 7;

  const cells: (number | null)[] = [
    ...Array.from({ length: leadingBlanks }, () => null),
    ...Array.from({ length: daysInMonth }, (_, i) => i + 1),
  ];

  const todayKey = ymd(today);
  const selectedEvents = selected ? (byDay.get(selected) ?? []) : [];

  const shiftMonth = (delta: number) => {
    setCursor(new Date(year, month + delta, 1));
    setSelected(null);
  };

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
      <div className="rounded-2xl border border-border bg-surface p-5">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-foreground">
            {MONTHS[month]} {year}
          </h2>
          <div className="flex gap-1">
            <button
              onClick={() => shiftMonth(-1)}
              aria-label="Previous month"
              className="grid h-9 w-9 place-items-center rounded-lg border border-border bg-surface text-muted transition hover:border-accent hover:text-foreground"
            >
              ←
            </button>
            <button
              onClick={() => {
                setCursor(new Date(today.getFullYear(), today.getMonth(), 1));
                setSelected(null);
              }}
              className="rounded-lg border border-border bg-surface px-3 text-sm text-muted transition hover:border-accent hover:text-foreground"
            >
              Today
            </button>
            <button
              onClick={() => shiftMonth(1)}
              aria-label="Next month"
              className="grid h-9 w-9 place-items-center rounded-lg border border-border bg-surface text-muted transition hover:border-accent hover:text-foreground"
            >
              →
            </button>
          </div>
        </div>

        <div className="mb-2 grid grid-cols-7 gap-1 text-center text-xs font-medium text-muted">
          {WEEKDAYS.map((d) => (
            <div key={d} className="py-1">
              {d}
            </div>
          ))}
        </div>

        <div className="grid grid-cols-7 gap-1">
          {cells.map((day, i) => {
            if (day === null) return <div key={`b${i}`} />;
            const key = ymd(new Date(year, month, day));
            const dayEvents = byDay.get(key) ?? [];
            const hasEvents = dayEvents.length > 0;
            const isToday = key === todayKey;
            const isSelected = key === selected;
            return (
              <button
                key={key}
                onClick={() => setSelected(isSelected ? null : key)}
                disabled={!hasEvents}
                className={`relative flex aspect-square flex-col items-center justify-center rounded-lg border text-sm transition ${
                  isSelected
                    ? "border-accent bg-accent/15 text-foreground"
                    : hasEvents
                      ? "border-border bg-surface-2 text-foreground hover:border-accent"
                      : "border-transparent text-muted"
                } ${isToday ? "ring-1 ring-accent/60" : ""}`}
              >
                {day}
                {hasEvents && (
                  <span className="mt-0.5 flex gap-0.5">
                    {dayEvents.slice(0, 3).map((e, idx) => (
                      <span
                        key={idx}
                        className="h-1.5 w-1.5 rounded-full"
                        style={{ background: categoryStyle(e.category).accent }}
                      />
                    ))}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Day detail panel */}
      <div className="rounded-2xl border border-border bg-surface p-5">
        {!selected ? (
          <p className="text-sm text-muted">
            Select a highlighted day to see your marked events. Dots show events on a day.
          </p>
        ) : selectedEvents.length === 0 ? (
          <p className="text-sm text-muted">No events on this day.</p>
        ) : (
          <>
            <h3 className="mb-3 font-semibold text-foreground">
              {new Date(selected).toLocaleDateString("en-GB", {
                weekday: "long",
                day: "numeric",
                month: "long",
              })}
            </h3>
            <ul className="space-y-3">
              {selectedEvents.map((e) => {
                const style = categoryStyle(e.category);
                return (
                  <li key={e.id} className="rounded-xl border border-border bg-surface-2 p-3">
                    <Link
                      href={`/events/${e.id}`}
                      className="font-medium text-foreground hover:text-accent-hover"
                    >
                      {e.title}
                    </Link>
                    <div className="mt-1 flex items-center gap-2 text-xs text-muted">
                      <span style={{ color: style.accent }}>{style.icon}</span>
                      {formatTime(e.start_at)}
                      {e.venue ? ` · ${e.venue.name}` : ""}
                    </div>
                  </li>
                );
              })}
            </ul>
          </>
        )}
      </div>
    </div>
  );
}
