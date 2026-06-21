import { afterEach, describe, expect, it, vi } from "vitest";

import { getHealth, setAuthTokenProvider } from "@/lib/api";

afterEach(() => {
  setAuthTokenProvider(() => null);
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("apiFetch token attach", () => {
  it("attaches an Authorization header when a token is available", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ status: "ok" }),
    });
    vi.stubGlobal("fetch", fetchMock);
    setAuthTokenProvider(() => "tok123");

    await getHealth();

    expect(fetchMock).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: "Bearer tok123" }),
      }),
    );
  });

  it("omits the Authorization header when no token is available", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ status: "ok" }),
    });
    vi.stubGlobal("fetch", fetchMock);
    setAuthTokenProvider(() => null);

    await getHealth();

    expect(fetchMock).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        headers: expect.not.objectContaining({ Authorization: expect.anything() }),
      }),
    );
  });
});
