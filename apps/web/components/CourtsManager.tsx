"use client";

/**
 * Lists a gym's courts and (for organizers/admins) offers inline add / rename /
 * deactivate controls. Mutating controls are wrapped in `RoleGate`; the backend
 * remains the real authority. The list itself renders for everyone.
 */
import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";

import { RoleGate } from "@/components/RoleGate";
import {
  useCourts,
  useCreateCourt,
  useDeleteCourt,
  useUpdateCourt,
} from "@/hooks/useGyms";
import { ApiError } from "@/lib/api";
import { courtCreateSchema, type Court, type CourtCreate } from "@/lib/gyms";

function AddCourtForm({ gymId }: { gymId: string }) {
  const createCourt = useCreateCourt(gymId);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<CourtCreate>({
    resolver: zodResolver(courtCreateSchema),
    defaultValues: { name: "" },
  });

  async function onSubmit(values: CourtCreate) {
    setSubmitError(null);
    try {
      await createCourt.mutateAsync(values);
      reset();
    } catch (err) {
      setSubmitError(
        err instanceof ApiError ? err.message : "Could not add court.",
      );
    }
  }

  return (
    <form
      noValidate
      onSubmit={(e) => void handleSubmit(onSubmit)(e)}
      className="space-y-2"
    >
      <div className="flex items-start gap-2">
        <div className="flex-1">
          <label htmlFor="court-name" className="sr-only">
            Court name
          </label>
          <input
            id="court-name"
            placeholder="Court name"
            className="w-full rounded border border-neutral-300 px-3 py-2 text-sm focus:border-court focus:outline-none"
            {...register("name")}
          />
          {errors.name && (
            <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
          )}
        </div>
        <button
          type="submit"
          disabled={createCourt.isPending}
          className="rounded bg-court px-3 py-2 text-sm font-medium text-white hover:bg-court-dark disabled:opacity-50"
        >
          Add court
        </button>
      </div>
      {submitError && (
        <p role="alert" className="text-sm font-medium text-red-600">
          {submitError}
        </p>
      )}
    </form>
  );
}

function CourtRow({ gymId, court }: { gymId: string; court: Court }) {
  const updateCourt = useUpdateCourt(gymId);
  const deleteCourt = useDeleteCourt(gymId);
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(court.name);

  async function saveName() {
    const trimmed = name.trim();
    if (trimmed.length === 0 || trimmed === court.name) {
      setEditing(false);
      setName(court.name);
      return;
    }
    await updateCourt.mutateAsync({ id: court.id, input: { name: trimmed } });
    setEditing(false);
  }

  return (
    <li className="flex items-center justify-between gap-3 px-4 py-3">
      {editing ? (
        <input
          aria-label="Court name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="flex-1 rounded border border-neutral-300 px-2 py-1 text-sm focus:border-court focus:outline-none"
        />
      ) : (
        <span className="flex items-center gap-2">
          <span className="font-medium text-neutral-900">{court.name}</span>
          {!court.is_active && (
            <span className="rounded bg-neutral-100 px-2 py-0.5 text-xs font-medium text-neutral-500">
              Inactive
            </span>
          )}
        </span>
      )}

      <RoleGate anyOf={["organizer", "admin"]}>
        <span className="flex items-center gap-2 text-sm">
          {editing ? (
            <button
              type="button"
              onClick={() => void saveName()}
              disabled={updateCourt.isPending}
              className="font-medium text-court hover:underline disabled:opacity-50"
            >
              Save
            </button>
          ) : (
            <button
              type="button"
              onClick={() => setEditing(true)}
              className="font-medium text-court hover:underline"
            >
              Rename
            </button>
          )}
          <button
            type="button"
            onClick={() =>
              void updateCourt.mutateAsync({
                id: court.id,
                input: { is_active: !court.is_active },
              })
            }
            disabled={updateCourt.isPending}
            className="font-medium text-neutral-600 hover:underline disabled:opacity-50"
          >
            {court.is_active ? "Deactivate" : "Activate"}
          </button>
          <button
            type="button"
            onClick={() => void deleteCourt.mutateAsync(court.id)}
            disabled={deleteCourt.isPending}
            className="font-medium text-red-600 hover:underline disabled:opacity-50"
          >
            Delete
          </button>
        </span>
      </RoleGate>
    </li>
  );
}

export function CourtsManager({ gymId }: { gymId: string }) {
  const { data, isPending, isError, error, refetch } = useCourts(gymId);

  return (
    <section className="space-y-3">
      <h2 className="text-lg font-semibold">Courts</h2>

      {isPending && (
        <p role="status" className="text-neutral-500">
          Loading courts…
        </p>
      )}

      {isError && (
        <div role="alert" className="space-y-2">
          <p className="font-medium text-red-600">Could not load courts</p>
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

      {data &&
        (data.length === 0 ? (
          <p className="text-neutral-500">No courts yet.</p>
        ) : (
          <ul className="divide-y divide-neutral-200 rounded-lg border border-neutral-200 bg-white">
            {data.map((court) => (
              <CourtRow key={court.id} gymId={gymId} court={court} />
            ))}
          </ul>
        ))}

      <RoleGate anyOf={["organizer", "admin"]}>
        <AddCourtForm gymId={gymId} />
      </RoleGate>
    </section>
  );
}
