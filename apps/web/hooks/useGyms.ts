"use client";

/**
 * TanStack Query wrappers for gyms & courts. Query keys are namespaced so
 * mutations can invalidate the right slices of cache (list vs. one gym vs. its
 * courts). Thin by design — all data shaping lives in `lib/gyms.ts`.
 */
import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseQueryResult,
} from "@tanstack/react-query";

import {
  createCourt,
  createGym,
  deleteCourt,
  deleteGym,
  getGym,
  listCourts,
  listGyms,
  updateCourt,
  updateGym,
  type Court,
  type CourtCreate,
  type CourtUpdate,
  type Gym,
  type GymCreate,
  type GymPage,
  type GymUpdate,
  type ListGymsParams,
} from "@/lib/gyms";

export const gymKeys = {
  all: ["gyms"] as const,
  list: (params: ListGymsParams) => ["gyms", "list", params] as const,
  detail: (id: string) => ["gyms", "detail", id] as const,
  courts: (gymId: string) => ["gyms", gymId, "courts"] as const,
};

export function useGyms(params: ListGymsParams = {}): UseQueryResult<GymPage> {
  return useQuery({
    queryKey: gymKeys.list(params),
    queryFn: () => listGyms(params),
  });
}

export function useGym(id: string): UseQueryResult<Gym> {
  return useQuery({
    queryKey: gymKeys.detail(id),
    queryFn: () => getGym(id),
    enabled: id.length > 0,
  });
}

export function useCourts(gymId: string): UseQueryResult<Court[]> {
  return useQuery({
    queryKey: gymKeys.courts(gymId),
    queryFn: () => listCourts(gymId),
    enabled: gymId.length > 0,
  });
}

export function useCreateGym() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: GymCreate) => createGym(input),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: gymKeys.all });
    },
  });
}

export function useUpdateGym(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: GymUpdate) => updateGym(id, input),
    onSuccess: (gym) => {
      qc.setQueryData(gymKeys.detail(id), gym);
      void qc.invalidateQueries({ queryKey: gymKeys.all });
    },
  });
}

export function useDeleteGym() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteGym(id),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: gymKeys.all });
    },
  });
}

export function useCreateCourt(gymId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: CourtCreate) => createCourt(gymId, input),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: gymKeys.courts(gymId) });
    },
  });
}

export function useUpdateCourt(gymId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (args: { id: string; input: CourtUpdate }) =>
      updateCourt(args.id, args.input),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: gymKeys.courts(gymId) });
    },
  });
}

export function useDeleteCourt(gymId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteCourt(id),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: gymKeys.courts(gymId) });
    },
  });
}
