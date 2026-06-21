/**
 * Registration API layer: Zod schema (runtime validation, project convention)
 * and typed wrappers over `apiFetch`. The read schema mirrors the backend
 * `RegistrationRead`.
 *
 * Timestamps arrive as UTC ISO-8601 strings and are kept as `z.string()` here —
 * display-time formatting (into the gym's zone) lives in `lib/time.ts`. The
 * nullable scheduling fields (slot/arrival/play) are only populated once the
 * scheduler has assigned the player; the UI must guard them before rendering.
 */
import { z } from "zod";

import { ApiError, apiFetch } from "@/lib/api";

/** Registration lifecycle statuses, mirroring the backend enum. */
export const REGISTRATION_STATUSES = [
  "confirmed",
  "waitlisted",
  "checked_in",
  "cancelled",
  "no_show",
  "completed",
] as const;
export const registrationStatusSchema = z.enum(REGISTRATION_STATUSES);
export type RegistrationStatus = z.infer<typeof registrationStatusSchema>;

/** A registration as returned by the API (`RegistrationRead`). */
export const registrationSchema = z.object({
  id: z.string(),
  run_id: z.string(),
  player_user_id: z.string(),
  status: registrationStatusSchema,
  queue_position: z.number().nullable(),
  assigned_slot_number: z.number().nullable(),
  assigned_arrival_time: z.string().nullable(),
  estimated_play_time: z.string().nullable(),
  registered_at: z.string(),
  cancelled_at: z.string().nullable(),
  checked_in_at: z.string().nullable(),
});
export type Registration = z.infer<typeof registrationSchema>;

/** Register the current player for a run. Returns the created registration. */
export function registerForRun(runId: string): Promise<Registration> {
  return apiFetch(`/runs/${runId}/registrations`, registrationSchema, {
    method: "POST",
  });
}

/**
 * Fetch the caller's active registration for a run, or `null` if they have
 * none. The backend signals "not registered" with a 404, which we map to
 * `null` so callers can render the register CTA; any other error is rethrown.
 */
export async function getMyRegistration(
  runId: string,
): Promise<Registration | null> {
  try {
    return await apiFetch(
      `/runs/${runId}/registrations/me`,
      registrationSchema,
    );
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) return null;
    throw err;
  }
}

/**
 * Cancel the caller's own registration for a run. Backend responds 204 No
 * Content, so we validate with `z.void()` (see `apiFetch`'s 204 handling).
 */
export function cancelMyRegistration(runId: string): Promise<void> {
  return apiFetch(`/runs/${runId}/registrations/me`, z.void(), {
    method: "DELETE",
  });
}
