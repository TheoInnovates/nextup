"use client";

/**
 * Pure presentation of a run's roster: three sections (Confirmed / Waitlist /
 * No-shows). No auth or data hooks — handlers and busy state arrive as props so
 * this renders deterministically in tests. Mobile-friendly: single column with
 * large tap targets (`min-h-11`, `py-3`) on the attendance buttons.
 */
import { type RosterEntry, type RosterResponse } from "@/lib/roster";
import { formatInTimeZone } from "@/lib/time";

export interface RosterViewProps {
  roster: RosterResponse;
  gymTimeZone: string;
  onCheckIn: (registrationId: string) => void;
  onNoShow: (registrationId: string) => void;
  /** Registration id currently being checked in (for a per-row busy state). */
  checkingInId?: string | null;
  /** Registration id currently being marked no-show. */
  markingNoShowId?: string | null;
}

/** A confirmed player's card, with slot/arrival/play details + attendance. */
function ConfirmedRow({
  entry,
  gymTimeZone,
  onCheckIn,
  onNoShow,
  isCheckingIn,
  isMarkingNoShow,
}: {
  entry: RosterEntry;
  gymTimeZone: string;
  onCheckIn: (registrationId: string) => void;
  onNoShow: (registrationId: string) => void;
  isCheckingIn: boolean;
  isMarkingNoShow: boolean;
}) {
  const checkedIn = entry.status === "checked_in";
  const busy = isCheckingIn || isMarkingNoShow;

  return (
    <li className="space-y-2 px-4 py-3">
      <div className="flex items-baseline justify-between gap-3">
        <p className="font-medium text-neutral-900">
          {entry.player_display_name}
        </p>
        {entry.assigned_slot_number !== null && (
          <span className="shrink-0 text-sm text-neutral-500">
            Slot #{entry.assigned_slot_number}
          </span>
        )}
      </div>
      <dl className="space-y-0.5 text-sm text-neutral-600">
        {entry.assigned_arrival_time !== null && (
          <div className="flex justify-between gap-4">
            <dt className="text-neutral-500">Arrive by</dt>
            <dd className="text-right font-medium">
              {formatInTimeZone(entry.assigned_arrival_time, gymTimeZone)}
            </dd>
          </div>
        )}
        {entry.estimated_play_time !== null && (
          <div className="flex justify-between gap-4">
            <dt className="text-neutral-500">Expected to play</dt>
            <dd className="text-right font-medium">
              {formatInTimeZone(entry.estimated_play_time, gymTimeZone)}
            </dd>
          </div>
        )}
      </dl>
      {checkedIn ? (
        <p className="text-sm font-semibold text-green-700">Checked in ✓</p>
      ) : (
        <div className="flex flex-col gap-2 sm:flex-row">
          <button
            type="button"
            onClick={() => onCheckIn(entry.registration_id)}
            disabled={busy}
            className="min-h-11 flex-1 rounded bg-court px-4 py-3 text-sm font-semibold text-white hover:bg-court-dark disabled:opacity-50"
          >
            {isCheckingIn ? "Checking in…" : "Check in"}
          </button>
          <button
            type="button"
            onClick={() => onNoShow(entry.registration_id)}
            disabled={busy}
            className="min-h-11 rounded border border-red-300 px-4 py-3 text-sm font-medium text-red-600 hover:bg-red-50 disabled:opacity-50 sm:flex-initial"
          >
            {isMarkingNoShow ? "Marking…" : "No-show"}
          </button>
        </div>
      )}
    </li>
  );
}

/** A simple name row used for the waitlist and no-show sections. */
function NameRow({ entry, detail }: { entry: RosterEntry; detail?: string }) {
  return (
    <li className="flex items-center justify-between gap-3 px-4 py-3">
      <span className="font-medium text-neutral-900">
        {entry.player_display_name}
      </span>
      {detail && <span className="text-sm text-neutral-500">{detail}</span>}
    </li>
  );
}

function Section({
  title,
  count,
  children,
}: {
  title: string;
  count: number;
  children: React.ReactNode;
}) {
  return (
    <section className="space-y-2">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-neutral-500">
        {title} ({count})
      </h2>
      {children}
    </section>
  );
}

export function RosterView({
  roster,
  gymTimeZone,
  onCheckIn,
  onNoShow,
  checkingInId = null,
  markingNoShowId = null,
}: RosterViewProps) {
  return (
    <div className="space-y-6">
      <Section title="Confirmed" count={roster.confirmed.length}>
        {roster.confirmed.length === 0 ? (
          <p className="text-sm text-neutral-500">No confirmed players yet.</p>
        ) : (
          <ul className="divide-y divide-neutral-200 rounded-lg border border-neutral-200 bg-white">
            {roster.confirmed.map((entry) => (
              <ConfirmedRow
                key={entry.registration_id}
                entry={entry}
                gymTimeZone={gymTimeZone}
                onCheckIn={onCheckIn}
                onNoShow={onNoShow}
                isCheckingIn={checkingInId === entry.registration_id}
                isMarkingNoShow={markingNoShowId === entry.registration_id}
              />
            ))}
          </ul>
        )}
      </Section>

      <Section title="Waitlist" count={roster.waitlist.length}>
        {roster.waitlist.length === 0 ? (
          <p className="text-sm text-neutral-500">No one is waitlisted.</p>
        ) : (
          <ul className="divide-y divide-neutral-200 rounded-lg border border-neutral-200 bg-white">
            {roster.waitlist.map((entry) => (
              <NameRow
                key={entry.registration_id}
                entry={entry}
                detail={
                  entry.queue_position !== null
                    ? `#${entry.queue_position}`
                    : undefined
                }
              />
            ))}
          </ul>
        )}
      </Section>

      <Section title="No-shows" count={roster.no_show.length}>
        {roster.no_show.length === 0 ? (
          <p className="text-sm text-neutral-500">No no-shows.</p>
        ) : (
          <ul className="divide-y divide-neutral-200 rounded-lg border border-neutral-200 bg-white">
            {roster.no_show.map((entry) => (
              <NameRow key={entry.registration_id} entry={entry} />
            ))}
          </ul>
        )}
      </Section>
    </div>
  );
}
