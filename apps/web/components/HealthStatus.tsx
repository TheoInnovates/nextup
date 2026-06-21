"use client";

import { useQuery } from "@tanstack/react-query";

import { getHealth } from "@/lib/api";

/**
 * Phase 1 connectivity check: calls the API `/health` endpoint and renders the
 * loading / error / ready states (the loading/error/empty discipline reused by
 * every later feature).
 */
export function HealthStatus() {
  const { data, isPending, isError, error, refetch, isFetching } = useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
  });

  if (isPending) {
    return (
      <p role="status" className="text-neutral-500">
        Checking API…
      </p>
    );
  }

  if (isError) {
    return (
      <div role="alert" className="space-y-2">
        <p className="font-medium text-red-600">API unreachable</p>
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

  return (
    <p className="font-medium text-green-700">
      API is healthy{isFetching ? " (refreshing…)" : ""} — status:{" "}
      <span className="font-mono">{data.status}</span>
    </p>
  );
}
