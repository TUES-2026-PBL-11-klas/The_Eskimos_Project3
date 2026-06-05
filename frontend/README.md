# EventHub — Frontend

Next.js (App Router) + TypeScript + Tailwind CSS v4. Responsive light-themed UI for
browsing aggregated events, with an authenticated surface (saved events, calendar,
reminders, account).

> **Data source.** The API service is consumed at runtime, but while it is offline
> the app serves an in-memory **mock** that mirrors the documented API contract, so
> every screen works without a backend. Toggle with `EVENTHUB_USE_MOCK`
> (`true` = mock, default; `false` = call the real API at `API_BASE_URL`).

## Run locally (dev)

```bash
npm install
npm run dev          # http://localhost:3000
```

## Run isolated in Docker (no API, no local node_modules)

The container is fully self-contained: it builds a standalone Next.js bundle and
serves the mock data. It does **not** start the API or any database.

```bash
docker compose up --build -d     # http://localhost:3000
docker compose down              # stop
```

Or via the task runner (1:1 mirrors):

```bash
make up            # Linux/macOS
.\tasks.ps1 up     # Windows (PowerShell)
```

## Task runner

`Makefile` (Linux/macOS) and `tasks.ps1` (Windows) expose identical targets:

| Target | Action |
| --- | --- |
| `install` | `npm install` |
| `dev` | `npm run dev` |
| `build` | `npm run build` |
| `lint` | ESLint |
| `fmt` | ESLint `--fix` |
| `typecheck` | `tsc --noEmit` |
| `gen-api` | Regenerate `lib/api/schema.d.ts` from the live API's `/openapi.json` (API must be up) |
| `docker-build` | Build the image |
| `up` / `down` | Start / stop the container via Docker Compose |

## Configuration

Copy `.env.example` to `.env.local` (git-ignored). Keys:

- `API_BASE_URL` — server-only base URL for the API (used when `EVENTHUB_USE_MOCK=false`).
- `EVENTHUB_USE_MOCK` — `true` (default) serves mock data; `false` calls the API.
- `AUTH_COOKIE_NAME` — name of the session cookie (used by the real auth flow).

## Notes / known items

- **Auth is visual only right now.** Login/signup, saving, reminders, calendar and
  account run against a clearly-labelled client-side demo store (localStorage),
  standing in for the real httpOnly-cookie session + route-handler BFF, which
  requires the live API.
- **`notFound()` status.** Unknown event/category ids render a not-found UI but
  return HTTP 200 (a Next 16 App Router behavior for dynamically-rendered routes);
  truly unmatched paths return 404. To revisit during live-API integration.
