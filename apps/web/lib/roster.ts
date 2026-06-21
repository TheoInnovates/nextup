/**
 * Roster & attendance API layer: Zod schemas (runtime validation, project
 * convention) and typed wrappers over `apiFetch`. The roster response mirrors
 * the backend, splitting registrations into confirmed / waitlist / no-show.
 *
 * Timestamps arrive as UTC ISO-8601 strings and are kept as `z.string()` here —
 * display-time formatting (into the gym's zone) lives in `lib/time.ts`. The
 * nullable scheduling fields are only populated once the scheduler has assigned
 * the player; the UI must guard them before rendering.
 */
import { z } from "zod";

import { apiFetch } from "@/lib/api";
import {
  registrationSchema,
  registrationStatusSchema,
  type Registration,
} from "@/lib/registrations";

/** One player's row on a run's roster (`RosterEntry`). */
export const rosterEntrySchema = z.object({
  registration_id: z.string(),
  player_user_id: z.string(),
  player_display_name: z.string(),
  player_email: z.string(),
  status: registrationStatusSchema,
  queue_position: z.number().nullable(),
  assigned_slot_number: z.number().nullable(),
  assigned_arrival_time: z.string().nullable(),
  estimated_play_time: z.string().nullable(),
  checked_in_at: z.string().nullable(),
});
export type RosterEntry = z.infer<typeof rosterEntrySchema>;

/** A run's full roster, split by registration state. */
export const rosterResponseSchema = z.object({
  run_id: z.string(),
  confirmed: z.array(rosterEntrySchema),
  waitlist: z.array(rosterEntrySchema),
  no_show: z.array(rosterEntrySchema),
});
export type RosterResponse = z.infer<typeof rosterResponseSchema>;

/** Fetch the roster for a run (organizer/admin only — backend enforces). */
export function getRoster(runId: string): Promise<RosterResponse> {
  return apiFetch(`/runs/${runId}/roster`, rosterResponseSchema);
}

/** Mark a registration checked in; returns the updated registration. */
export function checkIn(
  runId: string,
  registrationId: string,
): Promise<Registration> {
  return apiFetch(
    `/runs/${runId}/registrations/${registrationId}/check-in`,
    registrationSchema,
    { method: "POST" },
  );
}

/** Mark a registration a no-show; returns the updated registration. */
export function markNoShow(
  runId: string,
  registrationId: string,
): Promise<Registration> {
  return apiFetch(
    `/runs/${runId}/registrations/${registrationId}/no-show`,
    registrationSchema,
    { method: "POST" },
  );
}
