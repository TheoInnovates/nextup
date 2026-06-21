"use client";

/**
 * Renders the runs list with the loading / error / empty / ready discipline
 * (mirrors `GymList`). Deliberately free of auth/RoleGate so it can be
 * unit-tested with only a mocked `fetch`.
 *
 * Times are shown in the VIEWER's local zone (clearly labelled): the list makes
 * a single `listRuns` call and does not fetch each run's gym. Gym-timezone
 * display lives on the detail page, which already fetches the gym.
 */
import Link from "next/link";

import { RunStatusBadge } from "@/components/RunStatusBadge";
import { useRuns } from "@/hooks/useRuns";
import { formatLocal } from "@/lib/time";

export function RunList() {
  const { data, isPending, isError, error, refetch } = useRuns();

  if (isPending) {
    return (
      <p role="status" className="text-neutral-500">
        Loading runs…
      </p>
    );
  }

  if (isError) {
    return (
      <div role="alert" className="space-y-2">
        <p className="font-medium text-red-600">Could not load runs</p>
        <p className="text-sm text-neutral-500">{error.message}</p>
        <button
          type="button"
          onClick={() => void refetch()}
          className="rounded bg-court px-3 py-1 text-sm font-medium text-white hover:bg-court-dark"
        >
          Retry
        </button>
      </div>
    );
  }

  if (data.items.length === 0) {
    return <p className="text-neutral-500">No runs yet.</p>;
  }

  return (
    <ul className="divide-y divide-neutral-200 rounded-lg border border-neutral-200 bg-white">
      {data.items.map((run) => (
        <li key={run.id}>
          <Link
            href={`/runs/${run.id}`}
            className="flex items-center justify-between gap-4 px-4 py-3 hover:bg-neutral-50"
          >
            <span>
              <span className="font-medium text-neutral-900">{run.title}</span>
              <span className="block text-sm text-neutral-500">
                {formatLocal(run.start_time)}{" "}
                <span className="text-neutral-400">(your local time)</span>
              </span>
            </span>
            <RunStatusBadge status={run.status} />
          </Link>
        </li>
      ))}
    </ul>
  );
}
