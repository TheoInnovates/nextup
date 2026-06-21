"use client";

/**
 * Renders the gyms list with the loading / error / empty / ready discipline
 * (mirrors `HealthStatus`). Deliberately free of auth/RoleGate so it can be
 * unit-tested with only a mocked `fetch`.
 */
import Link from "next/link";

import { useGyms } from "@/hooks/useGyms";

export function GymList() {
  const { data, isPending, isError, error, refetch } = useGyms();

  if (isPending) {
    return (
      <p role="status" className="text-neutral-500">
        Loading gyms…
      </p>
    );
  }

  if (isError) {
    return (
      <div role="alert" className="space-y-2">
        <p className="font-medium text-red-600">Could not load gyms</p>
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
    return (
      <p className="text-neutral-500">No gyms yet.</p>
    );
  }

  return (
    <ul className="divide-y divide-neutral-200 rounded-lg border border-neutral-200 bg-white">
      {data.items.map((gym) => (
        <li key={gym.id}>
          <Link
            href={`/gyms/${gym.id}`}
            className="flex items-center justify-between gap-4 px-4 py-3 hover:bg-neutral-50"
          >
            <span>
              <span className="font-medium text-neutral-900">{gym.name}</span>
              <span className="block text-sm text-neutral-500">
                {gym.city}, {gym.state}
              </span>
            </span>
            {!gym.is_active && (
              <span className="rounded bg-neutral-100 px-2 py-0.5 text-xs font-medium text-neutral-500">
                Inactive
              </span>
            )}
          </Link>
        </li>
      ))}
    </ul>
  );
}
