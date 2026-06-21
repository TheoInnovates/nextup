"use client";

/**
 * Player-facing registration UI for a run.
 *
 * Structured in three layers so the status display can be unit-tested without
 * mocking auth or fetch:
 *   - `RegistrationPanel`  — gates on run status + role (no data hooks).
 *   - `RegistrationLoader` — mounts the data hooks (only for a player viewing a
 *     published run) and wires the mutation into plain props.
 *   - `RegistrationStatusView` — pure presentation; all display branches live
 *     here and it receives the registration + timezone as props.
 */
import { RoleGate } from "@/components/RoleGate";
import {
  useCancelRegistration,
  useMyRegistration,
  useRegister,
} from "@/hooks/useRegistration";
import { ApiError } from "@/lib/api";
import {
  type Registration,
  type RegistrationStatus,
} from "@/lib/registrations";
import { type Run } from "@/lib/runs";
import { formatInTimeZone, formatLocal } from "@/lib/time";

/** Friendly messages for the registration error codes the API can return. */
const ERROR_MESSAGES: Record<string, string> = {
  already_registered: "You're already registered for this run.",
  registration_not_open: "Registration for this run hasn't opened yet.",
  registration_closed: "Registration for this run has closed.",
};

const GENERIC_ERROR = "Could not register. Please try again.";

/** Map a thrown error to a user-facing message (by API code where possible). */
export function registrationErrorMessage(err: unknown): string {
  if (err instanceof ApiError && err.code) {
    return ERROR_MESSAGES[err.code] ?? GENERIC_ERROR;
  }
  return GENERIC_ERROR;
}

/**
 * Format a UTC instant for display: in the gym's IANA zone when known,
 * otherwise in the viewer's local zone. The label tells the reader which.
 */
function FormattedTime({
  iso,
  timeZone,
}: {
  iso: string;
  timeZone?: string;
}) {
  if (timeZone) {
    return (
      <>
        {formatInTimeZone(iso, timeZone)}{" "}
        <span className="text-neutral-400">(gym time)</span>
      </>
    );
  }
  return (
    <>
      {formatLocal(iso)} <span className="text-neutral-400">(your time)</span>
    </>
  );
}

/** Statuses an active registration can have — i.e. one the player may cancel. */
const ACTIVE_STATUSES: ReadonlySet<RegistrationStatus> = new Set([
  "confirmed",
  "waitlisted",
  "checked_in",
]);

/** A small "Cancel registration" button; rendered only when `onCancel` is set. */
function CancelButton({
  onCancel,
  isCancelling,
}: {
  onCancel: () => void;
  isCancelling: boolean;
}) {
  return (
    <button
      type="button"
      onClick={onCancel}
      disabled={isCancelling}
      className="rounded border border-red-300 px-3 py-1 text-sm font-medium text-red-600 hover:bg-red-50 disabled:opacity-50"
    >
      {isCancelling ? "Cancelling…" : "Cancel registration"}
    </button>
  );
}

export interface RegistrationStatusViewProps {
  registration: Registration | null;
  gymTimeZone?: string;
  onRegister: () => void;
  isRegistering: boolean;
  registerErrorMessage: string | null;
  /** When provided, an active registration shows a "Cancel registration" button. */
  onCancel?: () => void;
  isCancelling?: boolean;
  cancelErrorMessage?: string | null;
}

/**
 * Pure presentation of the caller's registration state. Renders the register
 * CTA when not registered, or the appropriate status card otherwise. All
 * nullable scheduling fields are guarded so it never renders "Invalid Date"
 * or a `#null` position.
 */
export function RegistrationStatusView({
  registration,
  gymTimeZone,
  onRegister,
  isRegistering,
  registerErrorMessage,
  onCancel,
  isCancelling = false,
  cancelErrorMessage = null,
}: RegistrationStatusViewProps) {
  // The cancel affordance shows only when a handler is wired and the caller's
  // registration is in an active (cancellable) state.
  const showCancel =
    onCancel !== undefined &&
    registration !== null &&
    ACTIVE_STATUSES.has(registration.status);

  const cancelControls = showCancel ? (
    <div className="space-y-1 pt-1">
      <CancelButton onCancel={onCancel} isCancelling={isCancelling} />
      {cancelErrorMessage && (
        <p role="alert" className="text-sm font-medium text-red-600">
          {cancelErrorMessage}
        </p>
      )}
    </div>
  ) : null;

  if (registration === null) {
    return (
      <div className="space-y-2">
        <button
          type="button"
          onClick={onRegister}
          disabled={isRegistering}
          className="rounded bg-court px-4 py-2 text-sm font-medium text-white hover:bg-court-dark disabled:opacity-50"
        >
          {isRegistering ? "Registering…" : "Register for this run"}
        </button>
        {registerErrorMessage && (
          <p role="alert" className="text-sm font-medium text-red-600">
            {registerErrorMessage}
          </p>
        )}
      </div>
    );
  }

  if (registration.status === "confirmed") {
    return (
      <div className="space-y-2 rounded-lg border border-green-200 bg-green-50 p-4 text-sm text-green-900">
        <p className="font-semibold">You&apos;re confirmed.</p>
        {registration.assigned_slot_number !== null && (
          <p>
            <span className="text-green-700">Slot:</span> #
            {registration.assigned_slot_number}
          </p>
        )}
        {registration.assigned_arrival_time !== null && (
          <p>
            <span className="text-green-700">Arrive by:</span>{" "}
            <FormattedTime
              iso={registration.assigned_arrival_time}
              timeZone={gymTimeZone}
            />
          </p>
        )}
        {registration.estimated_play_time !== null && (
          <p>
            <span className="text-green-700">Expected to play:</span>{" "}
            <FormattedTime
              iso={registration.estimated_play_time}
              timeZone={gymTimeZone}
            />
          </p>
        )}
        {cancelControls}
      </div>
    );
  }

  if (registration.status === "waitlisted") {
    return (
      <div className="space-y-1 rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
        <p className="font-semibold">You&apos;re on the waitlist.</p>
        {registration.queue_position !== null ? (
          <p>You&apos;re #{registration.queue_position} on the waitlist.</p>
        ) : (
          <p>We&apos;ll let you know if a spot opens up.</p>
        )}
        {cancelControls}
      </div>
    );
  }

  // checked_in / cancelled / no_show / completed — show the raw status as a
  // short label (a RunStatusBadge would mislead: its enum is run lifecycle, not
  // registration status).
  return (
    <div className="space-y-2 rounded-lg border border-neutral-200 bg-white p-4 text-sm text-neutral-700">
      <div className="flex items-center gap-2">
        <span>Your registration status:</span>
        <span className="font-medium capitalize">
          {registration.status.replace(/_/g, " ")}
        </span>
      </div>
      {cancelControls}
    </div>
  );
}

/**
 * Mounts the data + mutation hooks. Rendered only inside the gated, published
 * branch so the my-registration query never fires for non-players or
 * non-published runs.
 */
function RegistrationLoader({
  run,
  gymTimeZone,
}: {
  run: Run;
  gymTimeZone?: string;
}) {
  const myRegistration = useMyRegistration(run.id);
  const register = useRegister(run.id);
  const cancel = useCancelRegistration(run.id);

  if (myRegistration.isPending) {
    return (
      <p role="status" className="text-sm text-neutral-500">
        Loading your registration…
      </p>
    );
  }

  if (myRegistration.isError) {
    return (
      <div role="alert" className="space-y-2 text-sm">
        <p className="font-medium text-red-600">
          Could not load your registration.
        </p>
        <button
          type="button"
          onClick={() => void myRegistration.refetch()}
          className="rounded bg-court px-3 py-1 font-medium text-white hover:bg-court-dark"
        >
          Retry
        </button>
      </div>
    );
  }

  // A lightweight confirm before cancelling; kept here (not in the pure view)
  // so the view stays deterministic in tests.
  function handleCancel() {
    if (window.confirm("Cancel your registration for this run?")) {
      cancel.mutate();
    }
  }

  return (
    <RegistrationStatusView
      registration={myRegistration.data}
      gymTimeZone={gymTimeZone}
      onRegister={() => register.mutate()}
      isRegistering={register.isPending}
      registerErrorMessage={
        register.isError ? registrationErrorMessage(register.error) : null
      }
      onCancel={handleCancel}
      isCancelling={cancel.isPending}
      cancelErrorMessage={
        cancel.isError ? "Could not cancel. Please try again." : null
      }
    />
  );
}

/**
 * Top-level registration panel for a run detail page. Shows nothing actionable
 * unless the run is published and the viewer is a player; the backend remains
 * the real authority for who may register.
 */
export function RegistrationPanel({
  run,
  gymTimeZone,
}: {
  run: Run;
  gymTimeZone?: string;
}) {
  return (
    <section className="space-y-2">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-neutral-500">
        Your spot
      </h2>
      {run.status !== "published" ? (
        <p className="text-sm text-neutral-400">
          Registration isn&apos;t open for this run.
        </p>
      ) : (
        <RoleGate
          anyOf={["player"]}
          fallback={
            <p className="text-sm text-neutral-400">
              Only players can register for runs.
            </p>
          }
        >
          <RegistrationLoader run={run} gymTimeZone={gymTimeZone} />
        </RoleGate>
      )}
    </section>
  );
}
