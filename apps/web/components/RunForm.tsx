"use client";

/**
 * Reusable run create/edit form (react-hook-form + Zod resolver).
 *
 * The form has its OWN schema (`runFormSchema`): the five timestamps are
 * `datetime-local` strings and the numbers are coerced from their string inputs.
 * On submit it converts the locals to UTC ISO-8601 (`new Date(local).toISOString()`)
 * and hands a `RunCreate`-shaped payload to the parent, which owns the mutation.
 * Keeping the API schema (`lib/runs.ts`) separate avoids validating partially
 * typed datetime-local values against the ISO contract.
 */
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { useGyms } from "@/hooks/useGyms";
import type { RunCreate } from "@/lib/runs";

const FIELD =
  "w-full rounded border border-neutral-300 px-3 py-2 text-sm focus:border-court focus:outline-none";
const LABEL = "block text-sm font-medium text-neutral-700";
const ERR = "mt-1 text-sm text-red-600";

/** Browser-side form schema: datetime-local strings + coerced integers. */
export const runFormSchema = z.object({
  gym_id: z.string().min(1, "Gym is required"),
  title: z.string().min(1, "Title is required").max(200),
  description: z.string().max(2000),
  start_time: z.string().min(1, "Start time is required"),
  end_time: z.string().min(1, "End time is required"),
  registration_opens_at: z.string().min(1, "Registration open time is required"),
  registration_closes_at: z
    .string()
    .min(1, "Registration close time is required"),
  cancellation_deadline: z.string().min(1, "Cancellation deadline is required"),
  maximum_players: z.coerce.number().int().min(2, "At least 2 players"),
  players_per_team: z.coerce.number().int().min(1, "At least 1 per team"),
  number_of_courts: z.coerce.number().int().min(1, "At least 1 court"),
  estimated_game_minutes: z.coerce.number().int().min(1, "At least 1 minute"),
  arrival_lead_minutes: z.coerce.number().int().min(0, "Cannot be negative"),
});
export type RunFormValues = z.infer<typeof runFormSchema>;

/** Convert a `datetime-local` value to a UTC ISO-8601 string. */
function localToUtcIso(local: string): string {
  return new Date(local).toISOString();
}

/** Build the API `RunCreate` body from validated form values. */
function toRunCreate(values: RunFormValues): RunCreate {
  return {
    gym_id: values.gym_id,
    title: values.title,
    description: values.description.trim() === "" ? undefined : values.description,
    start_time: localToUtcIso(values.start_time),
    end_time: localToUtcIso(values.end_time),
    registration_opens_at: localToUtcIso(values.registration_opens_at),
    registration_closes_at: localToUtcIso(values.registration_closes_at),
    cancellation_deadline: localToUtcIso(values.cancellation_deadline),
    maximum_players: values.maximum_players,
    players_per_team: values.players_per_team,
    number_of_courts: values.number_of_courts,
    estimated_game_minutes: values.estimated_game_minutes,
    arrival_lead_minutes: values.arrival_lead_minutes,
  };
}

const EMPTY: RunFormValues = {
  gym_id: "",
  title: "",
  description: "",
  start_time: "",
  end_time: "",
  registration_opens_at: "",
  registration_closes_at: "",
  cancellation_deadline: "",
  maximum_players: 10,
  players_per_team: 5,
  number_of_courts: 1,
  estimated_game_minutes: 12,
  arrival_lead_minutes: 15,
};

export interface RunFormProps {
  defaultValues?: Partial<RunFormValues>;
  /** Lock the gym picker (edit flow can't move a run between gyms). */
  lockGym?: boolean;
  submitLabel: string;
  onSubmit: (values: RunCreate) => Promise<void> | void;
  submitError?: string | null;
  isSubmitting?: boolean;
}

export function RunForm({
  defaultValues,
  lockGym = false,
  submitLabel,
  onSubmit,
  submitError,
  isSubmitting,
}: RunFormProps) {
  const gyms = useGyms();
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting: formSubmitting },
  } = useForm<RunFormValues>({
    resolver: zodResolver(runFormSchema),
    defaultValues: { ...EMPTY, ...defaultValues },
  });

  const busy = isSubmitting ?? formSubmitting;
  const lockedGymId = defaultValues?.gym_id;

  function handleValid(values: RunFormValues) {
    return onSubmit(toRunCreate(values));
  }

  return (
    <form
      noValidate
      onSubmit={(e) => void handleSubmit(handleValid)(e)}
      className="space-y-4"
    >
      <div>
        <label htmlFor="gym_id" className={LABEL}>
          Gym
        </label>
        {lockGym ? (
          // A run can't move between gyms after creation. Keep the value
          // registered (a `disabled` select submits as `undefined` in RHF) and
          // show the gym name as static text.
          <>
            <input type="hidden" {...register("gym_id")} />
            <p className="text-sm text-neutral-600">
              {gyms.data?.items.find((g) => g.id === lockedGymId)?.name ??
                lockedGymId ??
                "—"}
            </p>
          </>
        ) : (
          <select id="gym_id" className={FIELD} {...register("gym_id")}>
            <option value="">Select a gym…</option>
            {gyms.data?.items.map((gym) => (
              <option key={gym.id} value={gym.id}>
                {gym.name}
              </option>
            ))}
          </select>
        )}
        {gyms.isError && (
          <p className={ERR}>Could not load gyms; try refreshing.</p>
        )}
        {errors.gym_id && <p className={ERR}>{errors.gym_id.message}</p>}
      </div>

      <div>
        <label htmlFor="title" className={LABEL}>
          Title
        </label>
        <input id="title" className={FIELD} {...register("title")} />
        {errors.title && <p className={ERR}>{errors.title.message}</p>}
      </div>

      <div>
        <label htmlFor="description" className={LABEL}>
          Description
        </label>
        <textarea
          id="description"
          rows={2}
          className={FIELD}
          {...register("description")}
        />
        {errors.description && (
          <p className={ERR}>{errors.description.message}</p>
        )}
      </div>

      <p className="text-sm text-neutral-500">
        Times are entered in your local timezone and stored as UTC.
      </p>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div>
          <label htmlFor="start_time" className={LABEL}>
            Start time
          </label>
          <input
            id="start_time"
            type="datetime-local"
            className={FIELD}
            {...register("start_time")}
          />
          {errors.start_time && (
            <p className={ERR}>{errors.start_time.message}</p>
          )}
        </div>
        <div>
          <label htmlFor="end_time" className={LABEL}>
            End time
          </label>
          <input
            id="end_time"
            type="datetime-local"
            className={FIELD}
            {...register("end_time")}
          />
          {errors.end_time && <p className={ERR}>{errors.end_time.message}</p>}
        </div>
        <div>
          <label htmlFor="registration_opens_at" className={LABEL}>
            Registration opens
          </label>
          <input
            id="registration_opens_at"
            type="datetime-local"
            className={FIELD}
            {...register("registration_opens_at")}
          />
          {errors.registration_opens_at && (
            <p className={ERR}>{errors.registration_opens_at.message}</p>
          )}
        </div>
        <div>
          <label htmlFor="registration_closes_at" className={LABEL}>
            Registration closes
          </label>
          <input
            id="registration_closes_at"
            type="datetime-local"
            className={FIELD}
            {...register("registration_closes_at")}
          />
          {errors.registration_closes_at && (
            <p className={ERR}>{errors.registration_closes_at.message}</p>
          )}
        </div>
        <div>
          <label htmlFor="cancellation_deadline" className={LABEL}>
            Cancellation deadline
          </label>
          <input
            id="cancellation_deadline"
            type="datetime-local"
            className={FIELD}
            {...register("cancellation_deadline")}
          />
          {errors.cancellation_deadline && (
            <p className={ERR}>{errors.cancellation_deadline.message}</p>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
        <div>
          <label htmlFor="maximum_players" className={LABEL}>
            Max players
          </label>
          <input
            id="maximum_players"
            type="number"
            min={2}
            className={FIELD}
            {...register("maximum_players")}
          />
          {errors.maximum_players && (
            <p className={ERR}>{errors.maximum_players.message}</p>
          )}
        </div>
        <div>
          <label htmlFor="players_per_team" className={LABEL}>
            Players / team
          </label>
          <input
            id="players_per_team"
            type="number"
            min={1}
            className={FIELD}
            {...register("players_per_team")}
          />
          {errors.players_per_team && (
            <p className={ERR}>{errors.players_per_team.message}</p>
          )}
        </div>
        <div>
          <label htmlFor="number_of_courts" className={LABEL}>
            Courts
          </label>
          <input
            id="number_of_courts"
            type="number"
            min={1}
            className={FIELD}
            {...register("number_of_courts")}
          />
          {errors.number_of_courts && (
            <p className={ERR}>{errors.number_of_courts.message}</p>
          )}
        </div>
        <div>
          <label htmlFor="estimated_game_minutes" className={LABEL}>
            Game minutes
          </label>
          <input
            id="estimated_game_minutes"
            type="number"
            min={1}
            className={FIELD}
            {...register("estimated_game_minutes")}
          />
          {errors.estimated_game_minutes && (
            <p className={ERR}>{errors.estimated_game_minutes.message}</p>
          )}
        </div>
        <div>
          <label htmlFor="arrival_lead_minutes" className={LABEL}>
            Arrival lead (min)
          </label>
          <input
            id="arrival_lead_minutes"
            type="number"
            min={0}
            className={FIELD}
            {...register("arrival_lead_minutes")}
          />
          {errors.arrival_lead_minutes && (
            <p className={ERR}>{errors.arrival_lead_minutes.message}</p>
          )}
        </div>
      </div>

      {submitError && (
        <p role="alert" className="text-sm font-medium text-red-600">
          {submitError}
        </p>
      )}

      <button
        type="submit"
        disabled={busy}
        className="rounded bg-court px-4 py-2 text-sm font-medium text-white hover:bg-court-dark disabled:opacity-50"
      >
        {busy ? "Saving…" : submitLabel}
      </button>
    </form>
  );
}
