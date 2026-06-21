/**
 * Run API layer: Zod schemas (runtime validation, project convention) and typed
 * wrappers over `apiFetch`. Read schema mirrors the backend `RunRead`; the
 * create/update bodies are separate, narrower shapes.
 *
 * Timestamps arrive as UTC ISO-8601 strings and are kept as `z.string()` here —
 * display-time formatting (into the gym's zone) lives in `lib/time.ts`, and the
 * create form converts `datetime-local` values to ISO before calling `createRun`.
 */
import { z } from "zod";

import { apiFetch } from "@/lib/api";

/** Run lifecycle statuses, in roughly chronological order. */
export const RUN_STATUSES = [
  "draft",
  "published",
  "registration_closed",
  "in_progress",
  "completed",
  "cancelled",
] as const;
export const runStatusSchema = z.enum(RUN_STATUSES);
export type RunStatus = z.infer<typeof runStatusSchema>;

/** A run as returned by the API (`RunRead`). */
export const runSchema = z.object({
  id: z.string(),
  gym_id: z.string(),
  organizer_user_id: z.string(),
  title: z.string(),
  description: z.string().nullable(),
  start_time: z.string(),
  end_time: z.string(),
  registration_opens_at: z.string(),
  registration_closes_at: z.string(),
  cancellation_deadline: z.string(),
  maximum_players: z.number(),
  players_per_team: z.number(),
  number_of_courts: z.number(),
  estimated_game_minutes: z.number(),
  arrival_lead_minutes: z.number(),
  status: runStatusSchema,
  created_at: z.string(),
  updated_at: z.string(),
});
export type Run = z.infer<typeof runSchema>;

/** Paginated list envelope for `GET /runs`. */
export const runPageSchema = z.object({
  items: z.array(runSchema),
  total: z.number(),
  limit: z.number(),
  offset: z.number(),
});
export type RunPage = z.infer<typeof runPageSchema>;

/**
 * Create-run body (backend `RunCreate`). The five timestamps are UTC ISO-8601
 * strings; the form is responsible for converting its `datetime-local` inputs
 * before calling `createRun`. Numeric bounds mirror the backend constraints.
 */
export const runCreateSchema = z.object({
  gym_id: z.string().min(1, "Gym is required"),
  title: z.string().min(1, "Title is required").max(200),
  description: z.string().max(2000).optional(),
  start_time: z.string().min(1, "Start time is required"),
  end_time: z.string().min(1, "End time is required"),
  registration_opens_at: z.string().min(1, "Registration open time is required"),
  registration_closes_at: z
    .string()
    .min(1, "Registration close time is required"),
  cancellation_deadline: z.string().min(1, "Cancellation deadline is required"),
  maximum_players: z.number().int().min(2, "At least 2 players"),
  players_per_team: z.number().int().min(1, "At least 1 player per team"),
  number_of_courts: z.number().int().min(1, "At least 1 court"),
  estimated_game_minutes: z.number().int().min(1, "At least 1 minute"),
  arrival_lead_minutes: z.number().int().min(0, "Cannot be negative"),
});
export type RunCreate = z.infer<typeof runCreateSchema>;

/** Update-run body: all fields optional; mirrors the backend `RunUpdate`. */
export const runUpdateSchema = runCreateSchema.partial();
export type RunUpdate = z.infer<typeof runUpdateSchema>;

const JSON_HEADERS = { "Content-Type": "application/json" } as const;

export interface ListRunsParams {
  gymId?: string;
  limit?: number;
  offset?: number;
}

export function listRuns(params: ListRunsParams = {}): Promise<RunPage> {
  const query = new URLSearchParams();
  if (params.gymId !== undefined) query.set("gym_id", params.gymId);
  if (params.limit !== undefined) query.set("limit", String(params.limit));
  if (params.offset !== undefined) query.set("offset", String(params.offset));
  const qs = query.toString();
  return apiFetch(`/runs${qs ? `?${qs}` : ""}`, runPageSchema);
}

export function getRun(id: string): Promise<Run> {
  return apiFetch(`/runs/${id}`, runSchema);
}

export function createRun(input: RunCreate): Promise<Run> {
  return apiFetch("/runs", runSchema, {
    method: "POST",
    body: JSON.stringify(input),
    headers: JSON_HEADERS,
  });
}

export function updateRun(id: string, input: RunUpdate): Promise<Run> {
  return apiFetch(`/runs/${id}`, runSchema, {
    method: "PATCH",
    body: JSON.stringify(input),
    headers: JSON_HEADERS,
  });
}

export function deleteRun(id: string): Promise<void> {
  return apiFetch(`/runs/${id}`, z.void(), { method: "DELETE" });
}

/** POST a lifecycle transition (`publish` | `cancel` | `start` | `complete`). */
function transition(id: string, action: string): Promise<Run> {
  return apiFetch(`/runs/${id}/${action}`, runSchema, { method: "POST" });
}

export function publishRun(id: string): Promise<Run> {
  return transition(id, "publish");
}

export function cancelRun(id: string): Promise<Run> {
  return transition(id, "cancel");
}

export function startRun(id: string): Promise<Run> {
  return transition(id, "start");
}

export function completeRun(id: string): Promise<Run> {
  return transition(id, "complete");
}

/** Lifecycle transitions, keyed by their POST action verb. */
export const RUN_TRANSITIONS = [
  "publish",
  "cancel",
  "start",
  "complete",
] as const;
export type RunTransitionAction = (typeof RUN_TRANSITIONS)[number];

/**
 * The lifecycle actions an owner/admin may take from each status. Terminal
 * states (`completed`, `cancelled`) offer none. Mirrors the backend's allowed
 * transitions — the backend remains the real authority.
 */
export const ALLOWED_TRANSITIONS: Record<RunStatus, RunTransitionAction[]> = {
  draft: ["publish", "cancel"],
  published: ["start", "cancel"],
  registration_closed: ["start", "cancel"],
  in_progress: ["complete", "cancel"],
  completed: [],
  cancelled: [],
};

/** Human label for a transition button. */
export const TRANSITION_LABELS: Record<RunTransitionAction, string> = {
  publish: "Publish",
  cancel: "Cancel",
  start: "Start",
  complete: "Complete",
};
