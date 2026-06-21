import { screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { GymList } from "@/components/GymList";
import { renderWithClient } from "@/tests/test-utils";

function mockFetchOnce(body: unknown, ok = true, status = 200) {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({ ok, status, json: async () => body }),
  );
}

function gym(id: string, name: string) {
  return {
    id,
    name,
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
  };
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("GymList", () => {
  it("shows a loading state first", () => {
    mockFetchOnce({ items: [], total: 0, limit: 50, offset: 0 });
    renderWithClient(<GymList />);
    expect(screen.getByRole("status")).toHaveTextContent(/loading gyms/i);
  });

  it("renders gym items from the API", async () => {
    mockFetchOnce({
      items: [gym("a", "Downtown Rec"), gym("b", "Uptown Courts")],
      total: 2,
      limit: 50,
      offset: 0,
    });
    renderWithClient(<GymList />);
    await waitFor(() =>
      expect(screen.getByText("Downtown Rec")).toBeInTheDocument(),
    );
    expect(screen.getByText("Uptown Courts")).toBeInTheDocument();
  });

  it("shows the empty state when there are no gyms", async () => {
    mockFetchOnce({ items: [], total: 0, limit: 50, offset: 0 });
    renderWithClient(<GymList />);
    await waitFor(() =>
      expect(screen.getByText(/no gyms yet/i)).toBeInTheDocument(),
    );
  });

  it("renders an error state when the API call fails", async () => {
    mockFetchOnce({ detail: "boom", code: "error" }, false, 500);
    renderWithClient(<GymList />);
    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent(/could not load gyms/i),
    );
  });
});
