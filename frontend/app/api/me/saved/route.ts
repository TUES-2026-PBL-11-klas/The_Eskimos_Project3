// BFF: GET  /api/me/saved        → API GET  /me/saved (list)
//      POST /api/me/saved {event_id} → API POST /me/saved/{event_id} (save)

import { forward } from "@/lib/api/bff";

export async function GET(): Promise<Response> {
  return forward("/me/saved");
}

export async function POST(request: Request): Promise<Response> {
  const { event_id } = await request.json();
  return forward(`/me/saved/${event_id}`, { method: "POST" });
}
