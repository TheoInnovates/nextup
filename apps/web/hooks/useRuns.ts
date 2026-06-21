"use client";

/**
 * TanStack Query wrappers for runs. Query keys are namespaced so mutations and
 * lifecycle transitions can invalidate the right slices of cache (list vs. one
 * run). Thin by design — all data shaping lives in `lib/runs.ts`.
 */
import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseQueryResult,
} from "@tanstack/react-query";

import {
  cancelRun,
  completeRun,
  createRun,
  deleteRun,
  getRun,
  listRuns,
  publishRun,
  startRun,
  updateRun,
  type ListRunsParams,
  type Run,
  type RunCreate,
  type RunPage,
  type RunTransitionAction,
  type RunUpdate,
} from "@/lib/runs";

export const runKeys = {
  all: ["runs"] as const,
  list: (params: ListRunsParams) => ["runs", "list", params] as const,
  detail: (id: string) => ["runs", "detail", id] as const,
};

export function useRuns(params: ListRunsParams = {}): UseQueryResult<RunPage> {
  return useQuery({
    queryKey: runKeys.list(params),
    queryFn: () => listRuns(params),
  });
}

export function useRun(id: string): UseQueryResult<Run> {
  return useQuery({
    queryKey: runKeys.detail(id),
    queryFn: () => getRun(id),
    enabled: id.length > 0,
  });
}

export function useCreateRun() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: RunCreate) => createRun(input),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: runKeys.all });
    },
  });
}

export function useUpdateRun(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: RunUpdate) => updateRun(id, input),
    onSuccess: (run) => {
      qc.setQueryData(runKeys.detail(id), run);
      void qc.invalidateQueries({ queryKey: runKeys.all });
    },
  });
}

export function useDeleteRun() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteRun(id),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: runKeys.all });
    },
  });
}

const TRANSITION_FNS: Record<RunTransitionAction, (id: string) => Promise<Run>> =
  {
    publish: publishRun,
    cancel: cancelRun,
    start: startRun,
    complete: completeRun,
  };

/**
 * One mutation covering all four lifecycle transitions for a run; pass the
 * action when calling `mutateAsync`. Updates the detail cache and invalidates
 * lists on success.
 */
export function useRunTransition(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (action: RunTransitionAction) => TRANSITION_FNS[action](id),
    onSuccess: (run) => {
      qc.setQueryData(runKeys.detail(id), run);
      void qc.invalidateQueries({ queryKey: runKeys.all });
    },
  });
}
