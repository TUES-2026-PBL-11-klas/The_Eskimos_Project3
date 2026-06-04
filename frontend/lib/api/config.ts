// Central API/data configuration.

/** Server-only base URL for the API service. */
export const API_BASE_URL = process.env.API_BASE_URL ?? "http://localhost:8000";

/** Name of the httpOnly cookie holding the API session token (Phase 5). */
export const AUTH_COOKIE_NAME = process.env.AUTH_COOKIE_NAME ?? "eventhub_session";

/**
 * While the API is unreachable we serve the documented shapes from an in-memory
 * mock so the visuals are fully exercised. Flip to live by setting
 * EVENTHUB_USE_MOCK=false (and having the API running). Defaults to mock.
 */
export const USE_MOCK = process.env.EVENTHUB_USE_MOCK !== "false";
