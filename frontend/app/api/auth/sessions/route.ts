// BFF: GET /api/auth/sessions → API GET /auth/sessions (active devices).

import { forward } from "@/lib/api/bff";

export async function GET(): Promise<Response> {
  return forward("/auth/sessions");
}
