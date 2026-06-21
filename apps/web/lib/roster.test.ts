import { describe, expect, it } from "vitest";

import { rosterEntrySchema, rosterResponseSchema } from "@/lib/roster";

const confirmed = {
  registration_id: "11111111-1111-1111-1111-111111111111",
  player_user_id: "22222222-2222-2222-2222-222222222222",
  player_display_name: "Alex Hooper",
  player_email: "alex@example.com",
  status: "confirmed",
  queue_position: null,
  assigned_slot_number: 4,
  assigned_arrival_time: "2026-06-23T21:45:00Z",
  estimated_play_time: "2026-06-23T22:00:00Z",
  checked_in_at: null,
};

const waitlisted = {
  ...confirmed,
  registration_id: "33333333-3333-3333-3333-333333333333",
  status: "waitlisted",
  queue_position: 2,
  assigned_slot_number: null,
  assigned_arrival_time: null,
  estimated_play_time: null,
};

describe("rosterEntrySchema", () => {
  it("parses a confirmed entry with scheduling fields", () => {
    const parsed = rosterEntrySchema.parse(confirmed);
    expect(parsed.status).toBe("confirmed");
    expect(parsed.assigned_slot_number).toBe(4);
  });

  it("parses a waitlisted entry with null scheduling fields", () => {
    const parsed = rosterEntrySchema.parse(waitlisted);
    expect(parsed.queue_position).toBe(2);
    expect(parsed.assigned_arrival_time).toBeNull();
  });

  it("rejects an unknown status", () => {
    expect(
      rosterEntrySchema.safeParse({ ...confirmed, status: "pending" }).success,
    ).toBe(false);
  });

  it("rejects a missing required field", () => {
    const { player_display_name: _omitted, ...rest } = confirmed;
    void _omitted;
    expect(rosterEntrySchema.safeParse(rest).success).toBe(false);
  });
});

describe("rosterResponseSchema", () => {
  it("parses a full roster split into three lists", () => {
    const parsed = rosterResponseSchema.parse({
      run_id: "44444444-4444-4444-4444-444444444444",
      confirmed: [confirmed],
      waitlist: [waitlisted],
      no_show: [],
    });
    expect(parsed.confirmed).toHaveLength(1);
    expect(parsed.waitlist).toHaveLength(1);
    expect(parsed.no_show).toHaveLength(0);
  });

  it("rejects a response missing a list", () => {
    expect(
      rosterResponseSchema.safeParse({
        run_id: "44444444-4444-4444-4444-444444444444",
        confirmed: [],
        waitlist: [],
      }).success,
    ).toBe(false);
  });
});
