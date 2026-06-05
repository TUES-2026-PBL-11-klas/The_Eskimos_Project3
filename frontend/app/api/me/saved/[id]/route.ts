// BFF: DELETE /api/me/saved/{savedId} → API DELETE /me/saved/{saved_id} (unsave).

import { forward } from "@/lib/api/bff";

export async function DELETE(
  _request: Request,
  { params }: { params: Promise<{ id: string }> },
): Promise<Response> {
  const { id } = await params;
  return forward(`/me/saved/${id}`, { method: "DELETE" });
}
