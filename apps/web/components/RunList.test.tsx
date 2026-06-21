import { screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { RunList } from "@/components/RunList";
import { renderWithClient } from "@/tests/test-utils";

function mockFetchOnce(body: unknown, ok = true, status = 200) {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({ ok, status, json: async () => body }),
  );
}

function run(id: string, title: string) {
  return {
    id,
    gym_id: "gym-1",
    organizer_user_id: "owner-1",
    title,
    description: null,
    start_time: "2026-06-23T22:00:00Z",
    end_time: "2026-06-24T00:00:00Z",
    registration_opens_at: "2026-06-20T12:00:00Z",
    registration_closes_at: "2026-06-23T20:00:00Z",
    cancellation_deadline: "2026-06-23T18:00:00Z",
    maximum_players: 15,
    players_per_team: 5,
    number_of_courts: 1,
    estimated_game_minutes: 12,
    arrival_lead_minutes: 15,
    status: "published",
    created_at: "2026-06-01T00:00:00Z",
    updated_at: "2026-06-01T00:00:00Z",
  };
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("RunList", () => {
  it("shows a loading state first", () => {
    mockFetchOnce({ items: [], total: 0, limit: 50, offset: 0 });
    renderWithClient(<RunList />);
    expect(screen.getByRole("status")).toHaveTextContent(/loading runs/i);
  });

  it("renders run items from the API", async () => {
    mockFetchOnce({
      items: [run("a", "Tuesday Run"), run("b", "Friday Run")],
      total: 2,
      limit: 50,
      offset: 0,
    });
    renderWithClient(<RunList />);
    await waitFor(() =>
      expect(screen.getByText("Tuesday Run")).toBeInTheDocument(),
    );
    expect(screen.getByText("Friday Run")).toBeInTheDocument();
  });

  it("shows the empty state when there are no runs", async () => {
    mockFetchOnce({ items: [], total: 0, limit: 50, offset: 0 });
    renderWithClient(<RunList />);
    await waitFor(() =>
      expect(screen.getByText(/no runs yet/i)).toBeInTheDocument(),
    );
  });

  it("renders an error state when the API call fails", async () => {
    mockFetchOnce({ detail: "boom", code: "error" }, false, 500);
    renderWithClient(<RunList />);
    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent(/could not load runs/i),
    );
  });
});
