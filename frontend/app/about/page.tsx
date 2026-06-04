import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "About",
  description:
    "EventHub aggregates events from across Bulgaria into one searchable place, de-duplicates them, and links you back to the original source.",
};

const STEPS = [
  {
    icon: "🛰️",
    title: "Collect",
    body: "An ingestion service regularly pulls listings from multiple public event sources — venue sites, ticketing pages and culture portals.",
  },
  {
    icon: "🧹",
    title: "Clean & de-duplicate",
    body: "The same concert often appears on several sites. We normalise titles, dates and venues and merge duplicates so each event shows up once.",
  },
  {
    icon: "🗂️",
    title: "Organise",
    body: "Events are tagged by category and linked to a venue and city, so you can filter and search across everything in one place.",
  },
  {
    icon: "🔗",
    title: "Link out",
    body: "EventHub never sells tickets. Every event links straight back to its original source for full details and booking.",
  },
];

const SOURCES = [
  "Venue & promoter websites",
  "Public ticketing platforms",
  "City culture & tourism portals",
  "Community and listings sites",
];

export default function AboutPage() {
  return (
    <main className="mx-auto max-w-4xl px-6 py-12">
      {/* Hero */}
      <section className="text-center">
        <span className="inline-block rounded-full border border-border bg-surface px-3 py-1 text-xs font-medium text-muted">
          About EventHub
        </span>
        <h1 className="mx-auto mt-5 max-w-2xl text-4xl font-bold tracking-tight text-foreground sm:text-5xl">
          Every event in Bulgaria, in one place
        </h1>
        <p className="mx-auto mt-5 max-w-2xl text-lg leading-relaxed text-muted">
          What&apos;s on this weekend? The answer is usually scattered across a dozen venue
          pages, ticketing sites and social feeds. EventHub gathers them into a single,
          searchable place — so you can spend less time hunting and more time going out.
        </p>
      </section>

      {/* The problem */}
      <section className="mt-16 grid gap-6 sm:grid-cols-2">
        <div className="rounded-2xl border border-border bg-surface p-6">
          <h2 className="text-lg font-semibold text-foreground">The problem</h2>
          <p className="mt-2 leading-relaxed text-muted">
            Event information is fragmented. Each venue and promoter publishes to its own
            site on its own schedule, and the same event is often listed in several places
            with slightly different details. There&apos;s no single view of what&apos;s
            happening near you.
          </p>
        </div>
        <div className="rounded-2xl border border-border bg-surface p-6">
          <h2 className="text-lg font-semibold text-foreground">Our approach</h2>
          <p className="mt-2 leading-relaxed text-muted">
            EventHub is an <span className="text-foreground">aggregator</span>, not an
            organiser. We continuously collect public listings, de-duplicate them into one
            clean record per event, and present them with consistent dates, venues and
            categories you can filter and search.
          </p>
        </div>
      </section>

      {/* How it works */}
      <section className="mt-16">
        <h2 className="text-2xl font-bold text-foreground">How it works</h2>
        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          {STEPS.map((step, i) => (
            <div
              key={step.title}
              className="flex gap-4 rounded-2xl border border-border bg-surface p-5"
            >
              <span className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-surface-2 text-xl">
                {step.icon}
              </span>
              <div>
                <h3 className="font-semibold text-foreground">
                  <span className="text-accent">{i + 1}.</span> {step.title}
                </h3>
                <p className="mt-1 text-sm leading-relaxed text-muted">{step.body}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Sources */}
      <section className="mt-16 rounded-2xl border border-border bg-surface p-6 sm:p-8">
        <h2 className="text-2xl font-bold text-foreground">Where the events come from</h2>
        <p className="mt-2 max-w-2xl leading-relaxed text-muted">
          We aggregate publicly available listings from a range of sources and always link
          back to the original. EventHub doesn&apos;t handle payments, tickets or bookings —
          those stay with the source.
        </p>
        <ul className="mt-5 grid gap-3 sm:grid-cols-2">
          {SOURCES.map((s) => (
            <li key={s} className="flex items-center gap-2 text-muted">
              <span className="text-accent">✓</span>
              {s}
            </li>
          ))}
        </ul>
      </section>

      {/* What EventHub is / isn't */}
      <section className="mt-8 grid gap-6 sm:grid-cols-2">
        <div className="rounded-2xl border border-success/30 bg-success/5 p-6">
          <h3 className="font-semibold text-foreground">What EventHub does</h3>
          <ul className="mt-3 space-y-2 text-sm text-muted">
            <li>• Brings events together in one searchable place</li>
            <li>• De-duplicates and organises by category, venue and city</li>
            <li>• Lets you save events and get reminders (once logged in)</li>
            <li>• Links you to the original source for the full details</li>
          </ul>
        </div>
        <div className="rounded-2xl border border-border bg-surface p-6">
          <h3 className="font-semibold text-foreground">What it doesn&apos;t do</h3>
          <ul className="mt-3 space-y-2 text-sm text-muted">
            <li>• Sell tickets or process payments</li>
            <li>• Create or host its own events</li>
            <li>• Replace the original source — it points you there</li>
          </ul>
        </div>
      </section>

      {/* CTA */}
      <section className="mt-16 rounded-2xl border border-border bg-surface-2 p-8 text-center">
        <h2 className="text-2xl font-bold text-foreground">Start exploring</h2>
        <p className="mx-auto mt-2 max-w-md text-muted">
          Browse what&apos;s happening soon, or search for something specific.
        </p>
        <div className="mt-6 flex flex-wrap justify-center gap-3">
          <Link
            href="/events"
            className="rounded-xl bg-accent px-5 py-2.5 font-semibold text-white transition hover:bg-accent-hover"
          >
            Browse events
          </Link>
          <Link
            href="/venues"
            className="rounded-xl border border-border bg-surface px-5 py-2.5 font-semibold text-foreground transition hover:border-accent"
          >
            Explore venues
          </Link>
        </div>
      </section>
    </main>
  );
}
