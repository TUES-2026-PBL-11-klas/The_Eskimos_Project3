// BFF: DELETE /api/auth/sessions/{id} → API DELETE /auth/sessions/{id} (revoke).

import { forward } from "@/lib/api/bff";

export async function DELETE(
  _request: Request,
  { params }: { params: Promise<{ id: string }> },
): Promise<Response> {
  const { id } = await params;
  return forward(`/auth/sessions/${id}`, { method: "DELETE" });
}
