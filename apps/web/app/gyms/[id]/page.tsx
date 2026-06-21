"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";

import { CourtsManager } from "@/components/CourtsManager";
import { GymForm } from "@/components/GymForm";
import { RoleGate } from "@/components/RoleGate";
import { useDeleteGym, useGym, useUpdateGym } from "@/hooks/useGyms";
import { ApiError } from "@/lib/api";
import type { Gym, GymCreate } from "@/lib/gyms";

function GymInfo({ gym }: { gym: Gym }) {
  return (
    <dl className="space-y-1 text-sm text-neutral-700">
      {gym.description && <p className="text-neutral-600">{gym.description}</p>}
      <p>
        {gym.address_line_1}
        {gym.address_line_2 ? `, ${gym.address_line_2}` : ""}
      </p>
      <p>
        {gym.city}, {gym.state} {gym.postal_code}
      </p>
      <p className="text-neutral-500">Timezone: {gym.timezone}</p>
      {!gym.is_active && (
        <p className="font-medium text-neutral-500">This gym is inactive.</p>
      )}
    </dl>
  );
}

function EditGymSection({ gym }: { gym: Gym }) {
  const router = useRouter();
  const updateGym = useUpdateGym(gym.id);
  const deleteGym = useDeleteGym();
  const [editing, setEditing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const defaults: Partial<GymCreate> = {
    name: gym.name,
    description: gym.description,
    address_line_1: gym.address_line_1,
    address_line_2: gym.address_line_2 ?? "",
    city: gym.city,
    state: gym.state,
    postal_code: gym.postal_code,
    timezone: gym.timezone,
  };

  async function handleUpdate(values: GymCreate) {
    setError(null);
    try {
      await updateGym.mutateAsync(values);
      setEditing(false);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not save gym.");
    }
  }

  async function handleDelete() {
    setError(null);
    try {
      await deleteGym.mutateAsync(gym.id);
      router.push("/gyms");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not delete gym.");
    }
  }

  if (editing) {
    return (
      <div className="space-y-3 rounded-lg border border-neutral-200 bg-white p-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Edit gym</h2>
          <button
            type="button"
            onClick={() => {
              setEditing(false);
              setError(null);
            }}
            className="text-sm font-medium text-neutral-600 hover:underline"
          >
            Cancel
          </button>
        </div>
        <GymForm
          defaultValues={defaults}
          submitLabel="Save changes"
          onSubmit={handleUpdate}
          submitError={error}
          isSubmitting={updateGym.isPending}
        />
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-3 text-sm">
        <button
          type="button"
          onClick={() => setEditing(true)}
          className="rounded border border-neutral-300 px-3 py-1 font-medium text-neutral-700 hover:bg-neutral-100"
        >
          Edit gym
        </button>
        <button
          type="button"
          onClick={() => void handleDelete()}
          disabled={deleteGym.isPending}
          className="rounded border border-red-300 px-3 py-1 font-medium text-red-600 hover:bg-red-50 disabled:opacity-50"
        >
          Delete gym
        </button>
      </div>
      {error && (
        <p role="alert" className="text-sm font-medium text-red-600">
          {error}
        </p>
      )}
    </div>
  );
}

export default function GymDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const { data: gym, isPending, isError, error, refetch } = useGym(id);

  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col gap-6 px-6 py-10">
      <div>
        <Link href="/gyms" className="text-sm text-court hover:underline">
          ← Gyms
        </Link>
      </div>

      {isPending && (
        <p role="status" className="text-neutral-500">
          Loading gym…
        </p>
      )}

      {isError && (
        <div role="alert" className="space-y-2">
          <p className="font-medium text-red-600">
            {error instanceof ApiError && error.status === 404
              ? "Gym not found"
              : "Could not load gym"}
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

      {gym && (
        <>
          <header className="space-y-3">
            <h1 className="text-2xl font-bold tracking-tight">{gym.name}</h1>
            <GymInfo gym={gym} />
            <RoleGate anyOf={["organizer", "admin"]}>
              <EditGymSection gym={gym} />
            </RoleGate>
          </header>

          <CourtsManager gymId={gym.id} />
        </>
      )}
    </main>
  );
}
