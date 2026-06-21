/**
 * Gym & Court API layer: Zod schemas (runtime validation, project convention)
 * and typed wrappers over `apiFetch`. Read schemas mirror the backend
 * `GymRead`/`CourtRead`; create/update are separate, narrower shapes.
 *
 * Timestamps and ids arrive as JSON strings and are kept as `z.string()` —
 * we don't reformat them here, so no need for stricter datetime parsing.
 */
import { z } from "zod";

import { apiFetch } from "@/lib/api";

/** A gym as returned by the API (`GymRead`). */
export const gymSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string(),
  address_line_1: z.string(),
  address_line_2: z.string().nullable(),
  city: z.string(),
  state: z.string(),
  postal_code: z.string(),
  timezone: z.string(),
  owner_user_id: z.string(),
  is_active: z.boolean(),
  created_at: z.string(),
  updated_at: z.string(),
});
export type Gym = z.infer<typeof gymSchema>;

/** A court as returned by the API (`CourtRead`). */
export const courtSchema = z.object({
  id: z.string(),
  gym_id: z.string(),
  name: z.string(),
  is_active: z.boolean(),
  created_at: z.string(),
  updated_at: z.string(),
});
export type Court = z.infer<typeof courtSchema>;

/** Paginated list envelope for `GET /gyms`. */
export const gymPageSchema = z.object({
  items: z.array(gymSchema),
  total: z.number(),
  limit: z.number(),
  offset: z.number(),
});
export type GymPage = z.infer<typeof gymPageSchema>;

export const courtListSchema = z.array(courtSchema);

/**
 * Create-gym input. `description` and `address_line_2` are optional (the server
 * defaults `description` to `""`). Validated client-side before submit.
 */
export const gymCreateSchema = z.object({
  name: z.string().min(1, "Name is required").max(200),
  description: z.string().max(2000).optional(),
  address_line_1: z.string().min(1, "Address is required").max(200),
  address_line_2: z.string().max(200).optional(),
  city: z.string().min(1, "City is required").max(120),
  state: z.string().min(1, "State is required").max(120),
  postal_code: z.string().min(1, "Postal code is required").max(20),
  timezone: z.string().min(1, "Timezone is required"),
});
export type GymCreate = z.infer<typeof gymCreateSchema>;

/** Update-gym input: all fields optional; mirrors the backend `GymUpdate`. */
export const gymUpdateSchema = gymCreateSchema.partial().extend({
  is_active: z.boolean().optional(),
});
export type GymUpdate = z.infer<typeof gymUpdateSchema>;

/** Create-court input: just a name (backend `CourtCreate`). */
export const courtCreateSchema = z.object({
  name: z.string().min(1, "Name is required").max(120),
});
export type CourtCreate = z.infer<typeof courtCreateSchema>;

/** Update-court input: rename and/or toggle active. */
export const courtUpdateSchema = z.object({
  name: z.string().min(1).max(120).optional(),
  is_active: z.boolean().optional(),
});
export type CourtUpdate = z.infer<typeof courtUpdateSchema>;

const JSON_HEADERS = { "Content-Type": "application/json" } as const;

export interface ListGymsParams {
  limit?: number;
  offset?: number;
}

export function listGyms(params: ListGymsParams = {}): Promise<GymPage> {
  const query = new URLSearchParams();
  if (params.limit !== undefined) query.set("limit", String(params.limit));
  if (params.offset !== undefined) query.set("offset", String(params.offset));
  const qs = query.toString();
  return apiFetch(`/gyms${qs ? `?${qs}` : ""}`, gymPageSchema);
}

export function getGym(id: string): Promise<Gym> {
  return apiFetch(`/gyms/${id}`, gymSchema);
}

export function createGym(input: GymCreate): Promise<Gym> {
  return apiFetch("/gyms", gymSchema, {
    method: "POST",
    body: JSON.stringify(input),
    headers: JSON_HEADERS,
  });
}

export function updateGym(id: string, input: GymUpdate): Promise<Gym> {
  return apiFetch(`/gyms/${id}`, gymSchema, {
    method: "PATCH",
    body: JSON.stringify(input),
    headers: JSON_HEADERS,
  });
}

export function deleteGym(id: string): Promise<void> {
  return apiFetch(`/gyms/${id}`, z.void(), { method: "DELETE" });
}

export function listCourts(gymId: string): Promise<Court[]> {
  return apiFetch(`/gyms/${gymId}/courts`, courtListSchema);
}

export function createCourt(gymId: string, input: CourtCreate): Promise<Court> {
  return apiFetch(`/gyms/${gymId}/courts`, courtSchema, {
    method: "POST",
    body: JSON.stringify(input),
    headers: JSON_HEADERS,
  });
}

export function updateCourt(id: string, input: CourtUpdate): Promise<Court> {
  return apiFetch(`/courts/${id}`, courtSchema, {
    method: "PATCH",
    body: JSON.stringify(input),
    headers: JSON_HEADERS,
  });
}

export function deleteCourt(id: string): Promise<void> {
  return apiFetch(`/courts/${id}`, z.void(), { method: "DELETE" });
}
