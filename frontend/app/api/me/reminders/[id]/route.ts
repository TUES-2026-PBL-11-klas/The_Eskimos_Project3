// BFF: DELETE /api/me/reminders/{id} → API DELETE /me/reminders/{id} (cancel).

import { forward } from "@/lib/api/bff";

export async function DELETE(
  _request: Request,
  { params }: { params: Promise<{ id: string }> },
): Promise<Response> {
  const { id } = await params;
  return forward(`/me/reminders/${id}`, { method: "DELETE" });
}
