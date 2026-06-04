// Stub auth used while the API is offline (visuals only).
//
// Simulates the documented /auth/login and /auth/register behaviour — including
// the 401 (bad credentials) and 409 (email exists) cases — so every form state
// is demonstrable. When the API is up, Phase 5-real replaces these with calls to
// the Next route-handler BFF (which sets the httpOnly session cookie, D3).
//
// Demo triggers:
//   - login with password "wrong"        → 401
//   - register with taken@example.com     → 409

import { ApiError } from "@/lib/api/types";

const delay = (ms: number) => new Promise((r) => setTimeout(r, ms));

export interface LoginInput {
  email: string;
  password: string;
}

export interface RegisterInput {
  email: string;
  password: string;
  display_name: string;
}

export async function mockLogin({ password }: LoginInput): Promise<void> {
  await delay(700);
  if (password === "wrong") {
    throw new ApiError(401, "Invalid email or password.");
  }
  // Success: the real client would set the session cookie here.
}

export async function mockRegister({ email }: RegisterInput): Promise<void> {
  await delay(700);
  if (email.trim().toLowerCase() === "taken@example.com") {
    throw new ApiError(409, "An account with this email already exists.");
  }
  // Success: the real client would create the account, then log in.
}
