"use client";

/**
 * TanStack Query wrappers for in-app notifications. Query keys are namespaced so
 * mutations (mark one / all read) can invalidate the list. Thin by design — all
 * data shaping lives in `lib/notifications.ts`.
 */
import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseMutationResult,
  type UseQueryResult,
} from "@tanstack/react-query";

import {
  listNotifications,
  markAllNotificationsRead,
  markNotificationRead,
  type ListNotificationsParams,
  type Notification,
  type NotificationPage,
} from "@/lib/notifications";

export const notificationKeys = {
  all: ["notifications"] as const,
  list: (params: ListNotificationsParams) =>
    ["notifications", "list", params] as const,
};

export function useNotifications(
  params: ListNotificationsParams = {},
): UseQueryResult<NotificationPage> {
  return useQuery({
    queryKey: notificationKeys.list(params),
    queryFn: () => listNotifications(params),
  });
}

/** Mark a single notification read, then invalidate the list. */
export function useMarkRead(): UseMutationResult<Notification, Error, string> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => markNotificationRead(id),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: notificationKeys.all });
    },
  });
}

/** Mark every notification read, then invalidate the list. */
export function useMarkAllRead(): UseMutationResult<void, Error, void> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => markAllNotificationsRead(),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: notificationKeys.all });
    },
  });
}
