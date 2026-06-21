import { screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { HealthStatus } from "@/components/HealthStatus";
import { renderWithClient } from "@/tests/test-utils";

function mockFetchOnce(response: Partial<Response> & { json: () => Promise<unknown> }) {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response));
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("HealthStatus", () => {
  it("shows a loading state first", () => {
    mockFetchOnce({
      ok: true,
      json: async () => ({ status: "ok" }),
    });
    renderWithClient(<HealthStatus />);
    expect(screen.getByRole("status")).toHaveTextContent(/checking api/i);
  });

  it("renders the healthy state when the API responds ok", async () => {
    mockFetchOnce({
      ok: true,
      json: async () => ({ status: "ok" }),
    });
    renderWithClient(<HealthStatus />);
    await waitFor(() =>
      expect(screen.getByText(/api is healthy/i)).toBeInTheDocument(),
    );
  });

  it("renders an error state when the API call fails", async () => {
    mockFetchOnce({
      ok: false,
      status: 503,
      json: async () => ({ detail: "not ready", code: "unavailable" }),
    });
    renderWithClient(<HealthStatus />);
    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent(/api unreachable/i),
    );
  });
});
