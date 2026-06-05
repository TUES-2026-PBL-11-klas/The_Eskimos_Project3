// BFF: POST /api/auth/register → API POST /auth/register, then auto-login so the
// new user lands authenticated with the session cookie set (D3). 409 (email
// already exists) and 422 are relayed for the form to surface.

import { NextResponse } from "next/server";

import { API_BASE_URL, AUTH_COOKIE_NAME } from "@/lib/api/config";

export async function POST(request: Request): Promise<NextResponse> {
  const { email, password, display_name } = await request.json();

  const reg = await fetch(`${API_BASE_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({ email, password, display_name }),
    cache: "no-store",
  });

  if (!reg.ok) {
    const body = await reg.json().catch(() => ({}));
    return NextResponse.json(
      { ok: false, error: body.detail ?? "Could not create the account." },
      { status: reg.status },
    );
  }

  // Account created — log in to obtain the session token.
  const login = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({ email, password }),
    cache: "no-store",
  });

  if (!login.ok) {
    // Registration succeeded but auto-login failed — let the user log in manually.
    return NextResponse.json({ ok: true, requiresLogin: true });
  }

  const data: { token: string; expires_at: string } = await login.json();
  const response = NextResponse.json({ ok: true });
  response.cookies.set(AUTH_COOKIE_NAME, data.token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    expires: new Date(data.expires_at),
  });
  return response;
}
