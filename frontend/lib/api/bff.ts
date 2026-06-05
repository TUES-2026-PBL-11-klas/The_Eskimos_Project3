// Server-only helpers shared by the Next route handlers (the BFF). The browser
// never calls the API directly: handlers read the opaque session token from the
// httpOnly cookie (D3) and forward it as a bearer, relaying the API's status/body.

import { cookies } from "next/headers";

import { API_BASE_URL, AUTH_COOKIE_NAME } from "./config";

/** Read the API session token from the httpOnly cookie (undefined if logged out). */
export async function getToken(): Promise<string | undefined> {
  const store = await cookies();
  return store.get(AUTH_COOKIE_NAME)?.value;
}

interface ForwardOpts {
  method?: string;
  body?: unknown;
  /** Attach the bearer token from the cookie (default true). */
  auth?: boolean;
}

/**
 * Forward a request to the API and return a Response mirroring its status and
 * body. Used by the proxy route handlers (saved, reminders, sessions, me).
 */
export async function forward(path: string, opts: ForwardOpts = {}): Promise<Response> {
  const { method = "GET", body, auth = true } = opts;

  const headers: Record<string, string> = { Accept: "application/json" };
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (auth) {
    const token = await getToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
    cache: "no-store",
  });

  const text = await res.text();
  return new Response(text.length > 0 ? text : null, {
    status: res.status,
    headers: { "Content-Type": res.headers.get("Content-Type") ?? "application/json" },
  });
}
