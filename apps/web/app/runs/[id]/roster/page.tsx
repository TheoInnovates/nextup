"use client";

/**
 * Organizer roster + check-in screen for a run. Mobile-friendly: single column,
 * large tap targets on the attendance buttons.
 *
 * Layered so the table can be unit-tested without mocking auth or fetch:
 *   - `RosterPage`   — resolves the run id, gates on role.
 *   - `RosterContent`— fetches the run + its gym (for the timezone).
 *   - `RosterLoader` — mounts the roster query + attendance mutations.
 *   - `RosterView`   — pure presentation (in `components/RosterView`); receives
 *     the roster + timezone + handlers. Kept out of this page module because
 *     Next.js only allows a default + config exports from a page file.
 */
import Link from "next/link";
import { useParams } from "next/navigation";

import { RoleGate } from "@/components/RoleGate";
import { RosterView } from "@/components/RosterView";
import { useGym } from "@/hooks/useGyms";
import { useCheckIn, useNoShow, useRoster } from "@/hooks/useRoster";
import { useRun } from "@/hooks/useRuns";
import { ApiError } from "@/lib/api";

/** Mounts the roster query + attendance mutations and wires them into props. */
function RosterLoader({ runId, gymTimeZone }: { runId: string; gymTimeZone: string }) {
  const roster = useRoster(runId);
  const checkIn = useCheckIn(runId);
  const noShow = useNoShow(runId);

  if (roster.isPending) {
    return (
      <p role="status" className="text-neutral-500">
        Loading roster…
      </p>
    );
  }

  if (roster.isError) {
    const notFound =
      roster.error instanceof ApiError && roster.error.status === 404;
    return (
      <div role="alert" className="space-y-2">
        <p className="font-medium text-red-600">
          {notFound ? "Roster not found" : "Could not load roster"}
        </p>
        <p className="text-sm text-neutral-500">{roster.error.message}</p>
        <button
          type="button"
          onClick={() => void roster.refetch()}
          className="rounded bg-court px-3 py-1 text-sm font-medium text-white hover:bg-court-dark"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <RosterView
      roster={roster.data}
      gymTimeZone={gymTimeZone}
      onCheckIn={(id) => checkIn.mutate(id)}
      onNoShow={(id) => noShow.mutate(id)}
      checkingInId={checkIn.isPending ? checkIn.variables : null}
      markingNoShowId={noShow.isPending ? noShow.variables : null}
    />
  );
}

/** Resolves the run + its gym (for the timezone) before rendering the roster. */
function RosterContent({ runId }: { runId: string }) {
  const run = useRun(runId);
  const gym = useGym(run.data?.gym_id ?? "");

  if (run.isPending) {
    return (
      <p role="status" className="text-neutral-500">
        Loading run…
      </p>
    );
  }

  if (run.isError) {
    const notFound = run.error instanceof ApiError && run.error.status === 404;
    return (
      <div role="alert" className="space-y-2">
        <p className="font-medium text-red-600">
          {notFound ? "Run not found" : "Could not load run"}
        </p>
        <p className="text-sm text-neutral-500">{run.error.message}</p>
        <button
          type="button"
          onClick={() => void run.refetch()}
          className="rounded bg-court px-3 py-1 text-sm font-medium text-white hover:bg-court-dark"
        >
          Retry
        </button>
      </div>
    );
  }

  if (gym.isPending) {
    return (
      <p role="status" className="text-neutral-500">
        Loading roster…
      </p>
    );
  }

  if (gym.isError) {
    return (
      <div role="alert" className="space-y-2">
        <p className="font-medium text-red-600">Could not load the gym</p>
        <p className="text-sm text-neutral-500">{gym.error.message}</p>
        <button
          type="button"
          onClick={() => void gym.refetch()}
          className="rounded bg-court px-3 py-1 text-sm font-medium text-white hover:bg-court-dark"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <>
      <header className="space-y-1">
        <h1 className="text-2xl font-bold tracking-tight">Roster</h1>
        <p className="text-neutral-600">{run.data.title}</p>
        <p className="text-xs text-neutral-400">
          Times shown in gym time ({gym.data.timezone}).
        </p>
      </header>
      <RosterLoader runId={runId} gymTimeZone={gym.data.timezone} />
    </>
  );
}

export default function RosterPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;

  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col gap-6 px-6 py-10">
      <div>
        <Link href={`/runs/${id}`} className="text-sm text-court hover:underline">
          ← Run
        </Link>
      </div>

      <RoleGate
        anyOf={["organizer", "admin"]}
        fallback={
          <p className="text-neutral-500">
            You&apos;re not authorized to view this roster.
          </p>
        }
      >
        <RosterContent runId={id} />
      </RoleGate>
    </main>
  );
}
