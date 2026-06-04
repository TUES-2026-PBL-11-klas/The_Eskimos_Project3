// In-memory mock dataset standing in for the API while it is unreachable.
// Mirrors the documented response shapes so the UI is fully exercised
// (browsing, filtering, search, pagination, calendar) without a backend.
//
// Dates are generated relative to "now" so "upcoming" / calendar always has
// fresh content. Swap `lib/api/endpoints.ts` to the live client when the API
// is up — no UI changes required.

import type { Category, EventSummary, Venue } from "./types";

const HOUR = 60 * 60 * 1000;
const DAY = 24 * HOUR;

/** Build an ISO datetime `days`/`hours` offset from now. */
function at(days: number, hours = 19): string {
  const d = new Date(Date.now() + days * DAY);
  d.setHours(hours, 0, 0, 0);
  return d.toISOString();
}

export const CATEGORIES: Category[] = [
  { name: "Music", slug: "music", count: 0 },
  { name: "Tech", slug: "tech", count: 0 },
  { name: "Art", slug: "art", count: 0 },
  { name: "Theatre", slug: "theatre", count: 0 },
  { name: "Sports", slug: "sports", count: 0 },
  { name: "Food & Drink", slug: "food", count: 0 },
  { name: "Film", slug: "film", count: 0 },
  { name: "Community", slug: "community", count: 0 },
];

export const VENUES: Venue[] = [
  { id: "v1", name: "Sofia Tech Park", city: "Sofia" },
  { id: "v2", name: "NDK — National Palace of Culture", city: "Sofia" },
  { id: "v3", name: "Arena Sofia", city: "Sofia" },
  { id: "v4", name: "Ivan Vazov National Theatre", city: "Sofia" },
  { id: "v5", name: "Plovdiv Roman Theatre", city: "Plovdiv" },
  { id: "v6", name: "Kapana Creative District", city: "Plovdiv" },
  { id: "v7", name: "Festival and Congress Center", city: "Varna" },
  { id: "v8", name: "Sea Garden Open Stage", city: "Varna" },
  { id: "v9", name: "Mall of Sofia", city: "Sofia" },
  { id: "v10", name: "Studio 5", city: "Sofia" },
];

function venue(id: string): Venue {
  return VENUES.find((v) => v.id === id)!;
}

interface Seed {
  title: string;
  category: string;
  venueId: string;
  days: number;
  hour?: number;
  description: string;
}

const SEEDS: Seed[] = [
  { title: "Sofia Synth Night: Modular Showcase", category: "Music", venueId: "v10", days: 1, hour: 21, description: "An evening of live modular synthesis from local and regional artists, with an open patch-bay session before the headline set." },
  { title: "JS Bulgaria Meetup — Edge Rendering", category: "Tech", venueId: "v1", days: 2, hour: 18, description: "Talks on streaming SSR, the App Router and edge runtimes, followed by pizza and networking." },
  { title: "Impressionists in Focus — Guided Tour", category: "Art", venueId: "v2", days: 2, hour: 17, description: "A curator-led walk through the touring impressionist collection, limited to 25 visitors." },
  { title: "Hamlet", category: "Theatre", venueId: "v4", days: 3, hour: 19, description: "A new staging of Shakespeare's tragedy by the national company." },
  { title: "Levski vs CSKA — City Derby", category: "Sports", venueId: "v3", days: 4, hour: 20, description: "The capital's biggest football rivalry returns for the spring fixture." },
  { title: "Natural Wine Tasting", category: "Food & Drink", venueId: "v6", days: 4, hour: 19, description: "Twelve low-intervention wines from small Balkan producers, paired with regional cheeses." },
  { title: "Open-Air Cinema: Past Lives", category: "Film", venueId: "v8", days: 5, hour: 21, description: "Seaside screening under the stars; bring a blanket." },
  { title: "Repair Café Sofia", category: "Community", venueId: "v9", days: 5, hour: 11, description: "Bring broken electronics, clothing or bikes and fix them with volunteer experts." },
  { title: "Balkan Brass Explosion", category: "Music", venueId: "v7", days: 6, hour: 20, description: "A high-energy night of brass bands from across the region." },
  { title: "AI & Robotics Demo Day", category: "Tech", venueId: "v1", days: 7, hour: 14, description: "Student and startup teams demo their latest builds; public welcome." },
  { title: "Street Art Walk — Kapana", category: "Art", venueId: "v6", days: 8, hour: 18, description: "Discover the murals of Plovdiv's creative quarter with a local guide." },
  { title: "The Cherry Orchard", category: "Theatre", venueId: "v5", days: 9, hour: 20, description: "Chekhov performed in the ancient Roman amphitheatre." },
  { title: "Vitosha Trail Run 12K", category: "Sports", venueId: "v3", days: 10, hour: 9, description: "A mountain trail race starting at the edge of the city." },
  { title: "Ramen Pop-Up Weekend", category: "Food & Drink", venueId: "v9", days: 11, hour: 12, description: "A two-day ramen residency from a visiting Tokyo chef." },
  { title: "Sofia Indie Film Festival — Opening", category: "Film", venueId: "v2", days: 12, hour: 19, description: "Opening gala and first screening block of the independent film festival." },
  { title: "Community Garden Build Day", category: "Community", venueId: "v8", days: 13, hour: 10, description: "Help build raised beds and plant the new neighbourhood garden." },
  { title: "Jazz at the Roman Theatre", category: "Music", venueId: "v5", days: 14, hour: 20, description: "An intimate quartet performance as the sun sets over Plovdiv." },
  { title: "Rust Workshop: Build a CLI", category: "Tech", venueId: "v1", days: 16, hour: 17, description: "Hands-on three-hour workshop; bring a laptop." },
  { title: "Ceramics Open Studio", category: "Art", venueId: "v10", days: 18, hour: 15, description: "Drop-in throwing and glazing session for all levels." },
  { title: "Stand-Up Comedy Showcase", category: "Theatre", venueId: "v9", days: 20, hour: 21, description: "Five comedians, one mic, one very long night." },
  { title: "Coastal Cycling Sportive", category: "Sports", venueId: "v7", days: 22, hour: 8, description: "A 60km ride along the Black Sea coast." },
  { title: "Craft Beer Festival", category: "Food & Drink", venueId: "v6", days: 24, hour: 16, description: "Forty breweries, live music and food trucks." },
  { title: "Classics Restored: Metropolis", category: "Film", venueId: "v4", days: 26, hour: 19, description: "The restored silent classic with live piano accompaniment." },
  { title: "Language Exchange Evening", category: "Community", venueId: "v9", days: 28, hour: 18, description: "Practice Bulgarian, English, German and more over coffee." },
  // A couple already in the past — used to verify "upcoming" filtering.
  { title: "Spring Choral Concert", category: "Music", venueId: "v2", days: -3, hour: 19, description: "Past event, kept to verify upcoming/past filtering." },
  { title: "Legacy DevOps Day", category: "Tech", venueId: "v1", days: -10, hour: 10, description: "Past event, kept to verify upcoming/past filtering." },
];

export const EVENTS: EventSummary[] = SEEDS.map((s, i) => ({
  id: `e${i + 1}`,
  title: s.title,
  start_at: at(s.days, s.hour),
  category: s.category,
  venue: venue(s.venueId),
}));

export const DESCRIPTIONS: Record<string, string> = Object.fromEntries(
  SEEDS.map((s, i) => [`e${i + 1}`, s.description]),
);

// Recompute category counts from the dataset.
for (const c of CATEGORIES) {
  c.count = EVENTS.filter((e) => e.category === c.name).length;
}
