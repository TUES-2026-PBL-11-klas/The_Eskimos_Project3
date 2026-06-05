// BFF: GET /api/me/reminders → API GET /me/reminders (all reminders).

import { forward } from "@/lib/api/bff";

export async function GET(): Promise<Response> {
  return forward("/me/reminders");
}
