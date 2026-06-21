"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";

import { RegistrationPanel } from "@/components/RegistrationPanel";
import { RoleGate } from "@/components/RoleGate";
import { RunStatusBadge } from "@/components/RunStatusBadge";
import { useGym } from "@/hooks/useGyms";
import { useRun, useRunTransition } from "@/hooks/useRuns";
import { ApiError } from "@/lib/api";
import {
  ALLOWED_TRANSITIONS,
  TRANSITION_LABELS,
  type Run,
} from "@/lib/runs";
import { formatInTimeZone } from "@/lib/time";

/** Labelled timestamp rows, each formatted in the gym's IANA timezone. */
function RunTimes({ run, timeZone }: { run: Run; timeZone: string }) {
  const rows: [string, string][] = [
    ["Starts", run.start_time],
    ["Ends", run.end_time],
    ["Registration opens", run.registration_opens_at],
    ["Registration closes", run.registration_closes_at],
    ["Cancellation deadline", run.cancellation_deadline],
  ];
  return (
    <dl className="space-y-1 text-sm text-neutral-700">
      {rows.map(([label, iso]) => (
        <div key={label} className="flex justify-between gap-4">
          <dt className="text-neutral-500">{label}</dt>
          <dd className="text-right font-medium">
            {formatInTimeZone(iso, timeZone)}
          </dd>
        </div>
      ))}
      <p className="pt-1 text-xs text-neutral-400">
        Times shown in gym time ({timeZone}).
      </p>
    </dl>
  );
}

function RunFacts({ run }: { run: Run }) {
  return (
    <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm text-neutral-700 sm:grid-cols-3">
      <Fact label="Max players" value={run.maximum_players} />
      <Fact label="Players / team" value={run.players_per_team} />
      <Fact label="Courts" value={run.number_of_courts} />
      <Fact label="Game minutes" value={run.estimated_game_minutes} />
      <Fact label="Arrival lead (min)" value={run.arrival_lead_minutes} />
    </dl>
  );
}

function Fact({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <dt className="text-neutral-500">{label}</dt>
      <dd className="font-medium">{value}</dd>
    </div>
  );
}

/** Owner/admin lifecycle + edit controls for a single run. */
function RunControls({ run }: { run: Run }) {
  const transition = useRunTransition(run.id);
  const [error, setError] = useState<string | null>(null);

  const actions = ALLOWED_TRANSITIONS[run.status];

  async function runTransition(action: (typeof actions)[number]) {
    setError(null);
    try {
      await transition.mutateAsync(action);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Could not update the run.",
      );
    }
  }

  const busy = transition.isPending;

  return (
    <div className="space-y-2 rounded-lg border border-neutral-200 bg-white p-4">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-neutral-500">
        Manage run
      </h2>
      <div className="flex flex-wrap items-center gap-2 text-sm">
        <Link
          href={`/runs/${run.id}/edit`}
          className="rounded border border-neutral-300 px-3 py-1 font-medium text-neutral-700 hover:bg-neutral-100"
        >
          Edit
        </Link>
        <Link
          href={`/runs/${run.id}/roster`}
          className="rounded border border-neutral-300 px-3 py-1 font-medium text-neutral-700 hover:bg-neutral-100"
        >
          Roster
        </Link>
        {actions.map((action) => (
          <button
            key={action}
            type="button"
            onClick={() => void runTransition(action)}
            disabled={busy}
            className={
              action === "cancel"
                ? "rounded border border-red-300 px-3 py-1 font-medium text-red-600 hover:bg-red-50 disabled:opacity-50"
                : "rounded border border-neutral-300 px-3 py-1 font-medium text-neutral-700 hover:bg-neutral-100 disabled:opacity-50"
            }
          >
            {TRANSITION_LABELS[action]}
          </button>
        ))}
      </div>
      {actions.length === 0 && (
        <p className="text-xs text-neutral-400">
          This run is in a terminal state; no further lifecycle changes are
          available.
        </p>
      )}
      {error && (
        <p role="alert" className="text-sm font-medium text-red-600">
          {error}
        </p>
      )}
    </div>
  );
}

function RunDetail({ run }: { run: Run }) {
  // The gym is fetched to obtain its IANA timezone for display. The hook's
  // `enabled` guard means this is a no-op until we have a gym id.
  const { data: gym, isPending: gymPending, isError: gymError } = useGym(
    run.gym_id,
  );

  return (
    <>
      <header className="space-y-2">
        <div className="flex items-center justify-between gap-3">
          <h1 className="text-2xl font-bold tracking-tight">{run.title}</h1>
          <RunStatusBadge status={run.status} />
        </div>
        {run.description && (
          <p className="text-neutral-600">{run.description}</p>
        )}
        <p className="text-sm text-neutral-500">
          Gym:{" "}
          <Link href={`/gyms/${run.gym_id}`} className="text-court hover:underline">
            {gym?.name ?? run.gym_id}
          </Link>
        </p>
      </header>

      {gym ? (
        // Times are formatted in the gym's configured IANA timezone.
        <RunTimes run={run} timeZone={gym.timezone} />
      ) : gymError ? (
        <p className="text-sm text-neutral-500">
          Could not load the gym, so times can&apos;t be shown in gym time.
        </p>
      ) : gymPending ? (
        <p role="status" className="text-neutral-500">
          Loading times…
        </p>
      ) : null}

      <RunFacts run={run} />

      <RegistrationPanel run={run} gymTimeZone={gym?.timezone} />

      <RoleGate anyOf={["organizer", "admin"]}>
        <RunControls run={run} />
      </RoleGate>
    </>
  );
}

export default function RunDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const { data: run, isPending, isError, error, refetch } = useRun(id);

  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col gap-6 px-6 py-10">
      <div>
        <Link href="/runs" className="text-sm text-court hover:underline">
          ← Runs
        </Link>
      </div>

      {isPending && (
        <p role="status" className="text-neutral-500">
          Loading run…
        </p>
      )}

      {isError && (
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
      )}

      {run && <RunDetail run={run} />}
    </main>
  );
}
