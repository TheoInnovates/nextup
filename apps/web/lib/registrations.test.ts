import { afterEach, describe, expect, it, vi } from "vitest";

import {
  getMyRegistration,
  registrationSchema,
} from "@/lib/registrations";

const confirmed = {
  id: "11111111-1111-1111-1111-111111111111",
  run_id: "22222222-2222-2222-2222-222222222222",
  player_user_id: "33333333-3333-3333-3333-333333333333",
  status: "confirmed",
  queue_position: null,
  assigned_slot_number: 4,
  assigned_arrival_time: "2026-06-23T21:45:00Z",
  estimated_play_time: "2026-06-23T22:00:00Z",
  registered_at: "2026-06-20T12:30:00Z",
  cancelled_at: null,
  checked_in_at: null,
};

const waitlisted = {
  ...confirmed,
  status: "waitlisted",
  queue_position: 3,
  assigned_slot_number: null,
  assigned_arrival_time: null,
  estimated_play_time: null,
};

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("registrationSchema", () => {
  it("parses a valid confirmed registration", () => {
    const parsed = registrationSchema.parse(confirmed);
    expect(parsed.status).toBe("confirmed");
    expect(parsed.assigned_slot_number).toBe(4);
  });

  it("parses a valid waitlisted registration", () => {
    const parsed = registrationSchema.parse(waitlisted);
    expect(parsed.status).toBe("waitlisted");
    expect(parsed.queue_position).toBe(3);
    expect(parsed.assigned_arrival_time).toBeNull();
  });

  it("rejects an unknown status", () => {
    expect(
      registrationSchema.safeParse({ ...confirmed, status: "pending" }).success,
    ).toBe(false);
  });
});

describe("getMyRegistration", () => {
  it("maps a 404 to null (not registered)", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 404,
        json: async () => ({ detail: "not found" }),
      }),
    );
    await expect(getMyRegistration("run-1")).resolves.toBeNull();
  });

  it("returns the registration on a 200", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => confirmed,
      }),
    );
    const result = await getMyRegistration("run-1");
    expect(result?.status).toBe("confirmed");
  });

  it("rethrows non-404 errors", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        json: async () => ({ detail: "boom" }),
      }),
    );
    await expect(getMyRegistration("run-1")).rejects.toThrow();
  });
});
