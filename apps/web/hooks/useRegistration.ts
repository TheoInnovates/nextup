"use client";

/**
 * TanStack Query wrappers for player registrations. Query keys are namespaced
 * per run so a successful register can invalidate the caller's own-registration
 * query (and the run detail, in case capacity counts are shown). Thin by design
 * — all data shaping lives in `lib/registrations.ts`.
 */
import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseMutationResult,
  type UseQueryResult,
} from "@tanstack/react-query";

import { runKeys } from "@/hooks/useRuns";
import {
  cancelMyRegistration,
  getMyRegistration,
  registerForRun,
  type Registration,
} from "@/lib/registrations";

export const registrationKeys = {
  all: ["registrations"] as const,
  mine: (runId: string) => ["registrations", "mine", runId] as const,
};

/**
 * The caller's registration for `runId`, or `null` when they have none (the
 * 404→null mapping happens in `getMyRegistration`). Disabled until a run id is
 * known so it doesn't fire with an empty path.
 */
export function useMyRegistration(
  runId: string,
): UseQueryResult<Registration | null> {
  return useQuery({
    queryKey: registrationKeys.mine(runId),
    queryFn: () => getMyRegistration(runId),
    enabled: runId.length > 0,
  });
}

/**
 * Register the caller for `runId`. On success, invalidates the caller's
 * own-registration query and the run detail (capacity counts may have changed).
 */
export function useRegister(
  runId: string,
): UseMutationResult<Registration, Error, void> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => registerForRun(runId),
    onSuccess: (registration) => {
      qc.setQueryData(registrationKeys.mine(runId), registration);
      void qc.invalidateQueries({ queryKey: runKeys.detail(runId) });
    },
  });
}

/**
 * Cancel the caller's registration for `runId`. On success, the player no
 * longer has an active registration, so we set the own-registration cache to
 * `null` (returns the panel to the not-registered state immediately) and
 * invalidate the run detail (capacity counts may have changed).
 */
export function useCancelRegistration(
  runId: string,
): UseMutationResult<void, Error, void> {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => cancelMyRegistration(runId),
    onSuccess: () => {
      qc.setQueryData(registrationKeys.mine(runId), null);
      void qc.invalidateQueries({ queryKey: runKeys.detail(runId) });
    },
  });
}
