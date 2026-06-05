// BFF: POST /api/auth/logout → API POST /auth/logout (revokes the session), then
// clears the cookie regardless of the API result.

import { NextResponse } from "next/server";

import { forward } from "@/lib/api/bff";
import { AUTH_COOKIE_NAME } from "@/lib/api/config";

export async function POST(): Promise<NextResponse> {
  await forward("/auth/logout", { method: "POST" }).catch(() => undefined);
  const response = NextResponse.json({ ok: true });
  response.cookies.delete(AUTH_COOKIE_NAME);
  return response;
}
