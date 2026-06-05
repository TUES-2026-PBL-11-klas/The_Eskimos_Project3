// BFF: GET /api/me/reminders/due → API GET /me/reminders/due (the on-load poll, D6).

import { forward } from "@/lib/api/bff";

export async function GET(): Promise<Response> {
  return forward("/me/reminders/due");
}
