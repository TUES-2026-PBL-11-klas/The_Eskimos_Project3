// Thin typed fetch client. READY for the live API but unused while USE_MOCK is on
// (the API is currently unreachable). Two entry points keep the bearer handling
// honest:
//   - serverFetch: runs in Server Components / route handlers; attaches the
//     bearer cookie when present.
//   - browserFetch: runs in client components; calls the Next route handlers
//     (the BFF), never the API's auth endpoints directly (D3).
//
// Both throw ApiError(status, ...) so callers can branch on 401 / 404 / 409.

import { API_BASE_URL } from "./config";
import { ApiError } from "./types";

type Query = Record<string, string | number | undefined | null>;

function buildUrl(base: string, path: string, query?: Query): string {
  const url = new URL(path.replace(/^\//, ""), base.endsWith("/") ? base : base + "/");
  if (query) {
    for (const [k, v] of Object.entries(query)) {
      if (v !== undefined && v !== null && v !== "") url.searchParams.set(k, String(v));
    }
  }
  return url.toString();
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    ...init,
    headers: { Accept: "application/json", ...init?.headers },
  });

  if (!res.ok) {
    let body: unknown;
    try {
      body = await res.json();
    } catch {
      body = await res.text().catch(() => undefined);
    }
    throw new ApiError(res.status, `Request failed: ${res.status} ${res.statusText}`, body);
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

/** Server-side call to the API, optionally with a bearer token. */
export function serverFetch<T>(
  path: string,
  opts: { query?: Query; bearer?: string; init?: RequestInit } = {},
): Promise<T> {
  const headers: Record<string, string> = {};
  if (opts.bearer) headers.Authorization = `Bearer ${opts.bearer}`;
  return request<T>(buildUrl(API_BASE_URL, path, opts.query), {
    ...opts.init,
    headers: { ...headers, ...opts.init?.headers },
  });
}

/** Client-side call routed through the Next BFF route handlers (relative URL). */
export function browserFetch<T>(path: string, init?: RequestInit): Promise<T> {
  return request<T>(path, init);
}
