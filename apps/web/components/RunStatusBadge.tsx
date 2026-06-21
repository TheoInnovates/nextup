/**
 * Small colored badge for a run's lifecycle status. Pure presentation — no data
 * fetching — so it renders the same on the list and detail pages.
 */
import type { RunStatus } from "@/lib/runs";

const STYLES: Record<RunStatus, string> = {
  draft: "bg-neutral-100 text-neutral-600",
  published: "bg-green-100 text-green-700",
  registration_closed: "bg-amber-100 text-amber-700",
  in_progress: "bg-court/15 text-court-dark",
  completed: "bg-blue-100 text-blue-700",
  cancelled: "bg-red-100 text-red-700",
};

const LABELS: Record<RunStatus, string> = {
  draft: "Draft",
  published: "Published",
  registration_closed: "Registration closed",
  in_progress: "In progress",
  completed: "Completed",
  cancelled: "Cancelled",
};

export function RunStatusBadge({ status }: { status: RunStatus }) {
  return (
    <span
      className={`inline-block rounded px-2 py-0.5 text-xs font-medium ${STYLES[status]}`}
    >
      {LABELS[status]}
    </span>
  );
}
