"use client";

/**
 * In-app notifications inbox.
 *
 * Shows the caller's notifications with the loading / error / empty discipline,
 * emphasises unread items, and offers per-item "Mark read" plus a "Mark all
 * read" action. Timestamps are shown in the viewer's local zone (clearly
 * labelled): notifications aren't tied to one gym, so there's no single zone to
 * format in.
 */
import Link from "next/link";

import {
  useMarkAllRead,
  useMarkRead,
  useNotifications,
} from "@/hooks/useNotifications";
import { type Notification } from "@/lib/notifications";
import { formatLocal } from "@/lib/time";

function NotificationCard({
  notification,
  onMarkRead,
  isMarkingRead,
}: {
  notification: Notification;
  onMarkRead: (id: string) => void;
  isMarkingRead: boolean;
}) {
  const unread = !notification.is_read;
  return (
    <li
      className={
        unread
          ? "space-y-1 border-l-4 border-court bg-court/5 px-4 py-3"
          : "space-y-1 px-4 py-3"
      }
    >
      <div className="flex items-start justify-between gap-3">
        <p
          className={
            unread
              ? "font-semibold text-neutral-900"
              : "font-medium text-neutral-700"
          }
        >
          {notification.title}
        </p>
        {unread && (
          <button
            type="button"
            onClick={() => onMarkRead(notification.id)}
            disabled={isMarkingRead}
            className="shrink-0 rounded border border-neutral-300 px-2 py-1 text-xs font-medium text-neutral-700 hover:bg-neutral-100 disabled:opacity-50"
          >
            Mark read
          </button>
        )}
      </div>
      <p className="text-sm text-neutral-600">{notification.message}</p>
      <p className="text-xs text-neutral-400">
        {formatLocal(notification.created_at)} (your local time)
        {notification.related_run_id && (
          <>
            {" · "}
            <Link
              href={`/runs/${notification.related_run_id}`}
              className="text-court hover:underline"
            >
              View run
            </Link>
          </>
        )}
      </p>
    </li>
  );
}

export default function NotificationsPage() {
  const { data, isPending, isError, error, refetch } = useNotifications();
  const markRead = useMarkRead();
  const markAllRead = useMarkAllRead();

  const hasUnread =
    data?.items.some((notification) => !notification.is_read) ?? false;

  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col gap-6 px-6 py-10">
      <div>
        <Link href="/" className="text-sm text-court hover:underline">
          ← Home
        </Link>
      </div>

      <header className="flex items-center justify-between gap-3">
        <h1 className="text-2xl font-bold tracking-tight">Notifications</h1>
        {hasUnread && (
          <button
            type="button"
            onClick={() => markAllRead.mutate()}
            disabled={markAllRead.isPending}
            className="rounded border border-neutral-300 px-3 py-1.5 text-sm font-medium text-neutral-700 hover:bg-neutral-100 disabled:opacity-50"
          >
            {markAllRead.isPending ? "Marking…" : "Mark all read"}
          </button>
        )}
      </header>

      {isPending && (
        <p role="status" className="text-neutral-500">
          Loading notifications…
        </p>
      )}

      {isError && (
        <div role="alert" className="space-y-2">
          <p className="font-medium text-red-600">
            Could not load notifications
          </p>
          <p className="text-sm text-neutral-500">{error.message}</p>
          <button
            type="button"
            onClick={() => void refetch()}
            className="rounded bg-court px-3 py-1 text-sm font-medium text-white hover:bg-court-dark"
          >
            Retry
          </button>
        </div>
      )}

      {data && data.items.length === 0 && (
        <p className="text-neutral-500">You have no notifications yet.</p>
      )}

      {data && data.items.length > 0 && (
        <ul className="divide-y divide-neutral-200 rounded-lg border border-neutral-200 bg-white">
          {data.items.map((notification) => (
            <NotificationCard
              key={notification.id}
              notification={notification}
              onMarkRead={(id) => markRead.mutate(id)}
              isMarkingRead={markRead.isPending}
            />
          ))}
        </ul>
      )}
    </main>
  );
}
