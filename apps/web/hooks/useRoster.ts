"use client";

/**
 * TanStack Query wrappers for a run's roster + attendance actions. Query keys
 * are namespaced per run so check-in / no-show mutations invalidate just that
 * run's roster. Thin by design — all data shaping lives in `lib/roster.ts`.
 */
import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseMutationResult,
  type UseQueryResult,
} from "@tanstack/react-query";

import { type Registration } from "@/lib/registrations";
import {
  checkIn,
  getRoster,
  markNoShow,
  type RosterResponse,
} from "@/lib/roster";

export const rosterKeys = {
  all: ["roster"] as const,
  detail: (runId: string) => ["roster", runId] as const,
};

export function useRoster(runId: string): UseQueryResult<RosterResponse> {
  return useQuery({
    queryKey: rosterKeys.detail(runId),
    queryFn: () => getRoster(runId),
    enabled: runId.length > 0,
  });
}

/** Check a player in; invalidates the run's roster so counts/states refresh. */
export function useCheckIn(
  runId: string,
): UseMutationResult<Registration, Error, string> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (registrationId: string) => checkIn(runId, registrationId),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: rosterKeys.detail(runId) });
    },
  });
}

/** Mark a player a no-show; invalidates the run's roster. */
export function useNoShow(
  runId: string,
): UseMutationResult<Registration, Error, string> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (registrationId: string) => markNoShow(runId, registrationId),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: rosterKeys.detail(runId) });
    },
  });
}
