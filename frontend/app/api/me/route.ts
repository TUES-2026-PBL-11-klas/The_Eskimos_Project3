// BFF: GET /api/me → API GET /me (profile + preferences);
//      PATCH /api/me → API PATCH /me (partial profile/preferences update).

import { forward } from "@/lib/api/bff";

export async function GET(): Promise<Response> {
  return forward("/me");
}

export async function PATCH(request: Request): Promise<Response> {
  const body = await request.json();
  return forward("/me", { method: "PATCH", body });
}
