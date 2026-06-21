import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { RunForm, type RunFormValues } from "@/components/RunForm";
import type { RunCreate } from "@/lib/runs";
import { renderWithClient } from "@/tests/test-utils";

// The gym select is populated by `useGyms`; stub the list response.
function stubGyms() {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        items: [
          {
            id: "gym-1",
            name: "Downtown Rec",
            description: "",
            address_line_1: "1 Main St",
            address_line_2: null,
            city: "Brooklyn",
            state: "NY",
            postal_code: "11201",
            timezone: "America/New_York",
            owner_user_id: "owner-1",
            is_active: true,
            created_at: "2026-01-01T00:00:00Z",
            updated_at: "2026-01-01T00:00:00Z",
          },
        ],
        total: 1,
        limit: 50,
        offset: 0,
      }),
    }),
  );
}

const fullDefaults: Partial<RunFormValues> = {
  gym_id: "gym-1",
  title: "Tuesday Run",
  description: "",
  // datetime-local-shaped strings (local wall clock, no zone suffix).
  start_time: "2026-06-23T18:00",
  end_time: "2026-06-23T20:00",
  registration_opens_at: "2026-06-20T08:00",
  registration_closes_at: "2026-06-23T16:00",
  cancellation_deadline: "2026-06-23T14:00",
  maximum_players: 15,
  players_per_team: 5,
  number_of_courts: 1,
  estimated_game_minutes: 12,
  arrival_lead_minutes: 15,
};

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("RunForm", () => {
  it("submits with the locked gym id and ISO-UTC timestamps", async () => {
    stubGyms();
    const onSubmit = vi.fn<(values: RunCreate) => void>();
    renderWithClient(
      <RunForm
        defaultValues={fullDefaults}
        lockGym
        submitLabel="Save changes"
        onSubmit={onSubmit}
      />,
    );

    await userEvent.click(screen.getByRole("button", { name: /save changes/i }));

    await waitFor(() => expect(onSubmit).toHaveBeenCalledTimes(1));
    const payload = onSubmit.mock.calls[0]![0];
    // The locked gym must still be submitted (a disabled select submits as
    // undefined; we register a hidden input instead).
    expect(payload.gym_id).toBe("gym-1");
    // Numbers are coerced, not strings.
    expect(payload.maximum_players).toBe(15);
    // datetime-local values are converted to UTC ISO-8601 with a Z suffix.
    expect(payload.start_time).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.*Z$/);
    expect(new Date(payload.start_time).toISOString()).toBe(payload.start_time);
  });

  it("blocks submit and shows an error when required fields are empty", async () => {
    stubGyms();
    const onSubmit = vi.fn<(values: RunCreate) => void>();
    renderWithClient(
      <RunForm submitLabel="Create run" onSubmit={onSubmit} />,
    );

    await userEvent.click(screen.getByRole("button", { name: /create run/i }));

    await waitFor(() =>
      expect(screen.getByText(/gym is required/i)).toBeInTheDocument(),
    );
    expect(onSubmit).not.toHaveBeenCalled();
  });
});
