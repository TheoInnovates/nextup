/**
 * Time-zone-aware display helpers.
 *
 * Timestamps are stored and returned by the API as UTC ISO-8601 strings. The
 * UI must DISPLAY them in the relevant gym's IANA timezone (project convention),
 * so these helpers wrap `Intl.DateTimeFormat` with an explicit `timeZone`.
 */

/** Default formatting: medium date + short time (e.g. "Jun 20, 2026, 2:00 PM"). */
const DEFAULT_OPTS: Intl.DateTimeFormatOptions = {
  dateStyle: "medium",
  timeStyle: "short",
};

/**
 * Formats a UTC ISO-8601 instant for display in `timeZone` (an IANA zone like
 * "America/New_York"). Pass `opts` to override the date/time styles. Returns the
 * original string if it can't be parsed, so callers never render "Invalid Date".
 */
export function formatInTimeZone(
  isoUtc: string,
  timeZone: string,
  opts: Intl.DateTimeFormatOptions = DEFAULT_OPTS,
): string {
  const date = new Date(isoUtc);
  if (Number.isNaN(date.getTime())) return isoUtc;
  return new Intl.DateTimeFormat(undefined, { ...opts, timeZone }).format(date);
}

/** Short variant: time only (e.g. "2:00 PM"), in the given zone. */
export function formatTimeInTimeZone(isoUtc: string, timeZone: string): string {
  return formatInTimeZone(isoUtc, timeZone, { timeStyle: "short" });
}

/**
 * Converts a UTC ISO-8601 instant to the `YYYY-MM-DDTHH:mm` string a
 * `datetime-local` input expects, expressed in the viewer's local zone. Used to
 * seed the edit form's defaults from a run's stored timestamps. Returns "" for
 * an unparseable value.
 */
export function isoToLocalInput(isoUtc: string): string {
  const date = new Date(isoUtc);
  if (Number.isNaN(date.getTime())) return "";
  const pad = (n: number) => String(n).padStart(2, "0");
  const yyyy = date.getFullYear();
  const mm = pad(date.getMonth() + 1);
  const dd = pad(date.getDate());
  const hh = pad(date.getHours());
  const min = pad(date.getMinutes());
  return `${yyyy}-${mm}-${dd}T${hh}:${min}`;
}

/**
 * Formats a UTC instant in the viewer's local zone (no explicit `timeZone`).
 * Used on the runs list, where the gym's zone isn't fetched (one query only);
 * the label should make the "local time" framing clear to the reader.
 */
export function formatLocal(
  isoUtc: string,
  opts: Intl.DateTimeFormatOptions = DEFAULT_OPTS,
): string {
  const date = new Date(isoUtc);
  if (Number.isNaN(date.getTime())) return isoUtc;
  return new Intl.DateTimeFormat(undefined, opts).format(date);
}
