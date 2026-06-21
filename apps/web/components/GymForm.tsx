"use client";

/**
 * Reusable gym create/edit form (react-hook-form + Zod resolver). The parent
 * supplies the submit handler (a mutation) so this component stays free of any
 * data-layer concern. `submitError` surfaces server failures above the button.
 */
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";

import { gymCreateSchema, type GymCreate } from "@/lib/gyms";

const FIELD =
  "w-full rounded border border-neutral-300 px-3 py-2 text-sm focus:border-court focus:outline-none";
const LABEL = "block text-sm font-medium text-neutral-700";
const ERR = "mt-1 text-sm text-red-600";

export interface GymFormProps {
  defaultValues?: Partial<GymCreate>;
  submitLabel: string;
  onSubmit: (values: GymCreate) => Promise<void> | void;
  submitError?: string | null;
  isSubmitting?: boolean;
}

export function GymForm({
  defaultValues,
  submitLabel,
  onSubmit,
  submitError,
  isSubmitting,
}: GymFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting: formSubmitting },
  } = useForm<GymCreate>({
    resolver: zodResolver(gymCreateSchema),
    defaultValues: {
      name: "",
      description: "",
      address_line_1: "",
      address_line_2: "",
      city: "",
      state: "",
      postal_code: "",
      timezone: "",
      ...defaultValues,
    },
  });

  const busy = isSubmitting ?? formSubmitting;

  return (
    <form
      noValidate
      onSubmit={(e) => void handleSubmit(onSubmit)(e)}
      className="space-y-4"
    >
      <div>
        <label htmlFor="name" className={LABEL}>
          Name
        </label>
        <input id="name" className={FIELD} {...register("name")} />
        {errors.name && <p className={ERR}>{errors.name.message}</p>}
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

      <div>
        <label htmlFor="address_line_1" className={LABEL}>
          Address line 1
        </label>
        <input
          id="address_line_1"
          className={FIELD}
          {...register("address_line_1")}
        />
        {errors.address_line_1 && (
          <p className={ERR}>{errors.address_line_1.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="address_line_2" className={LABEL}>
          Address line 2
        </label>
        <input
          id="address_line_2"
          className={FIELD}
          {...register("address_line_2")}
        />
        {errors.address_line_2 && (
          <p className={ERR}>{errors.address_line_2.message}</p>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="city" className={LABEL}>
            City
          </label>
          <input id="city" className={FIELD} {...register("city")} />
          {errors.city && <p className={ERR}>{errors.city.message}</p>}
        </div>
        <div>
          <label htmlFor="state" className={LABEL}>
            State
          </label>
          <input id="state" className={FIELD} {...register("state")} />
          {errors.state && <p className={ERR}>{errors.state.message}</p>}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="postal_code" className={LABEL}>
            Postal code
          </label>
          <input
            id="postal_code"
            className={FIELD}
            {...register("postal_code")}
          />
          {errors.postal_code && (
            <p className={ERR}>{errors.postal_code.message}</p>
          )}
        </div>
        <div>
          <label htmlFor="timezone" className={LABEL}>
            Timezone (IANA)
          </label>
          <input
            id="timezone"
            placeholder="America/New_York"
            className={FIELD}
            {...register("timezone")}
          />
          {errors.timezone && <p className={ERR}>{errors.timezone.message}</p>}
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
