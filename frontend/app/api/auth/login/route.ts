// BFF: POST /api/auth/login → API POST /auth/login. On success the opaque token
// is stored in an httpOnly cookie (D3); the browser never sees it.

import { NextResponse } from "next/server";

import { API_BASE_URL, AUTH_COOKIE_NAME } from "@/lib/api/config";

interface TokenResponse {
  token: string;
  expires_at: string;
}

export async function POST(request: Request): Promise<NextResponse> {
  const { email, password } = await request.json();

  const res = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({ email, password }),
    cache: "no-store",
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    return NextResponse.json(
      { ok: false, error: body.detail ?? "Invalid email or password." },
      { status: res.status },
    );
  }

  const data: TokenResponse = await res.json();
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
