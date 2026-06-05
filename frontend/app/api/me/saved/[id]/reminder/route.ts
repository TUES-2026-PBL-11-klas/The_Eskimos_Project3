// BFF: POST /api/me/saved/{savedId}/reminder → API POST /me/saved/{saved_id}/reminder.
// Body is { lead_hours? } or { remind_at? }; an empty body uses the user's default.

import { forward } from "@/lib/api/bff";

export async function POST(
  request: Request,
  { params }: { params: Promise<{ id: string }> },
): Promise<Response> {
  const { id } = await params;
  const body = await request.json().catch(() => ({}));
  return forward(`/me/saved/${id}/reminder`, { method: "POST", body });
}
