"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";

import { RoleGate } from "@/components/RoleGate";
import { RunForm, type RunFormValues } from "@/components/RunForm";
import { useRun, useUpdateRun } from "@/hooks/useRuns";
import { ApiError } from "@/lib/api";
import type { Run, RunCreate } from "@/lib/runs";
import { isoToLocalInput } from "@/lib/time";

function NotAuthorized() {
  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center gap-4 px-6 text-center">
      <p role="alert" className="font-medium text-red-600">
        You need an organizer account to edit a run.
      </p>
      <Link href="/runs" className="text-court underline">
        Back to runs
      </Link>
    </main>
  );
}

/** Form defaults derived from the run: ISO timestamps → datetime-local. */
function toFormDefaults(run: Run): Partial<RunFormValues> {
  return {
    gym_id: run.gym_id,
    title: run.title,
    description: run.description ?? "",
    start_time: isoToLocalInput(run.start_time),
    end_time: isoToLocalInput(run.end_time),
    registration_opens_at: isoToLocalInput(run.registration_opens_at),
    registration_closes_at: isoToLocalInput(run.registration_closes_at),
    cancellation_deadline: isoToLocalInput(run.cancellation_deadline),
    maximum_players: run.maximum_players,
    players_per_team: run.players_per_team,
    number_of_courts: run.number_of_courts,
    estimated_game_minutes: run.estimated_game_minutes,
    arrival_lead_minutes: run.arrival_lead_minutes,
  };
}

function EditRunForm({ run }: { run: Run }) {
  const router = useRouter();
  const updateRun = useUpdateRun(run.id);
  const [submitError, setSubmitError] = useState<string | null>(null);

  async function handleSubmit(values: RunCreate) {
    setSubmitError(null);
    try {
      await updateRun.mutateAsync(values);
      router.push(`/runs/${run.id}`);
    } catch (err) {
      setSubmitError(
        err instanceof ApiError ? err.message : "Could not save the run.",
      );
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col gap-6 px-6 py-10">
      <header>
        <Link
          href={`/runs/${run.id}`}
          className="text-sm text-court hover:underline"
        >
          ← Run
        </Link>
        <h1 className="mt-1 text-2xl font-bold tracking-tight">Edit run</h1>
      </header>
      <RunForm
        defaultValues={toFormDefaults(run)}
        lockGym
        submitLabel="Save changes"
        onSubmit={handleSubmit}
        submitError={submitError}
        isSubmitting={updateRun.isPending}
      />
    </main>
  );
}

function EditRunLoader() {
  const params = useParams<{ id: string }>();
  const { data: run, isPending, isError, error, refetch } = useRun(params.id);

  if (isPending) {
    return (
      <main className="mx-auto flex min-h-screen max-w-2xl flex-col gap-6 px-6 py-10">
        <p role="status" className="text-neutral-500">
          Loading run…
        </p>
      </main>
    );
  }

  if (isError) {
    return (
      <main className="mx-auto flex min-h-screen max-w-2xl flex-col gap-6 px-6 py-10">
        <div role="alert" className="space-y-2">
          <p className="font-medium text-red-600">
            {error instanceof ApiError && error.status === 404
              ? "Run not found"
              : "Could not load run"}
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
      </main>
    );
  }

  return <EditRunForm run={run} />;
}

/** Edit-run page, gated to organizers/admins (UX only; backend enforces). */
export default function EditRunPage() {
  return (
    <RoleGate anyOf={["organizer", "admin"]} fallback={<NotAuthorized />}>
      <EditRunLoader />
    </RoleGate>
  );
}
