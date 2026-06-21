/**
 * Notifications API layer: Zod schemas (runtime validation, project convention)
 * and typed wrappers over `apiFetch`. The read schema mirrors the backend
 * `NotificationRead`.
 *
 * Timestamps arrive as UTC ISO-8601 strings and are kept as `z.string()` here —
 * display-time formatting lives in `lib/time.ts`.
 */
import { z } from "zod";

import { apiFetch } from "@/lib/api";

/** Notification kinds the API can emit, mirroring the backend enum. */
export const NOTIFICATION_TYPES = [
  "waitlist_promoted",
  "run_cancelled",
  "time_changed",
  "registration_confirmed",
] as const;
export const notificationTypeSchema = z.enum(NOTIFICATION_TYPES);
export type NotificationType = z.infer<typeof notificationTypeSchema>;

/** A notification as returned by the API (`NotificationRead`). */
export const notificationSchema = z.object({
  id: z.string(),
  type: notificationTypeSchema,
  title: z.string(),
  message: z.string(),
  related_run_id: z.string().nullable(),
  is_read: z.boolean(),
  created_at: z.string(),
  read_at: z.string().nullable(),
});
export type Notification = z.infer<typeof notificationSchema>;

/** Paginated list envelope for `GET /notifications`. */
export const notificationPageSchema = z.object({
  items: z.array(notificationSchema),
  total: z.number(),
  limit: z.number(),
  offset: z.number(),
});
export type NotificationPage = z.infer<typeof notificationPageSchema>;

export interface ListNotificationsParams {
  limit?: number;
  offset?: number;
}

export function listNotifications(
  params: ListNotificationsParams = {},
): Promise<NotificationPage> {
  const query = new URLSearchParams();
  if (params.limit !== undefined) query.set("limit", String(params.limit));
  if (params.offset !== undefined) query.set("offset", String(params.offset));
  const qs = query.toString();
  return apiFetch(
    `/notifications${qs ? `?${qs}` : ""}`,
    notificationPageSchema,
  );
}

/** Mark one notification read; returns the updated notification. */
export function markNotificationRead(id: string): Promise<Notification> {
  return apiFetch(`/notifications/${id}/read`, notificationSchema, {
    method: "POST",
  });
}

/** Mark every notification read; backend responds 204 No Content. */
export function markAllNotificationsRead(): Promise<void> {
  return apiFetch(`/notifications/read-all`, z.void(), { method: "POST" });
}
