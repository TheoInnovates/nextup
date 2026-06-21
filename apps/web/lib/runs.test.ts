import { describe, expect, it } from "vitest";

import {
  ALLOWED_TRANSITIONS,
  runCreateSchema,
  runPageSchema,
  runSchema,
} from "@/lib/runs";

const validRun = {
  id: "11111111-1111-1111-1111-111111111111",
  gym_id: "22222222-2222-2222-2222-222222222222",
  organizer_user_id: "33333333-3333-3333-3333-333333333333",
  title: "Tuesday Night Run",
  description: "Competitive 5v5",
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

describe("runSchema", () => {
  it("parses a valid run", () => {
    expect(() => runSchema.parse(validRun)).not.toThrow();
  });

  it("accepts a null description", () => {
    expect(runSchema.parse({ ...validRun, description: null }).description).toBeNull();
  });

  it("fails on an unknown status", () => {
    expect(runSchema.safeParse({ ...validRun, status: "archived" }).success).toBe(
      false,
    );
  });

  it("fails when a required field is missing", () => {
    const { title: _omitted, ...withoutTitle } = validRun;
    void _omitted;
    expect(runSchema.safeParse(withoutTitle).success).toBe(false);
  });

  it("fails when maximum_players is not a number", () => {
    expect(
      runSchema.safeParse({ ...validRun, maximum_players: "15" }).success,
    ).toBe(false);
  });
});

describe("runPageSchema", () => {
  it("parses a paginated envelope", () => {
    const page = { items: [validRun], total: 1, limit: 50, offset: 0 };
    expect(runPageSchema.parse(page).items).toHaveLength(1);
  });

  it("parses an empty envelope", () => {
    const page = { items: [], total: 0, limit: 50, offset: 0 };
    expect(runPageSchema.parse(page).items).toHaveLength(0);
  });
});

describe("runCreateSchema", () => {
  const validCreate = {
    gym_id: "g1",
    title: "Run",
    start_time: "2026-06-23T22:00:00Z",
    end_time: "2026-06-24T00:00:00Z",
    registration_opens_at: "2026-06-20T12:00:00Z",
    registration_closes_at: "2026-06-23T20:00:00Z",
    cancellation_deadline: "2026-06-23T18:00:00Z",
    maximum_players: 10,
    players_per_team: 5,
    number_of_courts: 1,
    estimated_game_minutes: 12,
    arrival_lead_minutes: 15,
  };

  it("accepts a minimal valid payload (description omitted)", () => {
    expect(runCreateSchema.safeParse(validCreate).success).toBe(true);
  });

  it("rejects maximum_players below 2", () => {
    const result = runCreateSchema.safeParse({ ...validCreate, maximum_players: 1 });
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error.issues.map((i) => i.path[0])).toContain(
        "maximum_players",
      );
    }
  });

  it("rejects an empty title and missing gym", () => {
    const result = runCreateSchema.safeParse({
      ...validCreate,
      title: "",
      gym_id: "",
    });
    expect(result.success).toBe(false);
    if (!result.success) {
      const fields = result.error.issues.map((i) => i.path[0]);
      expect(fields).toContain("title");
      expect(fields).toContain("gym_id");
    }
  });
});

describe("ALLOWED_TRANSITIONS", () => {
  it("offers publish + cancel for a draft", () => {
    expect(ALLOWED_TRANSITIONS.draft).toEqual(["publish", "cancel"]);
  });

  it("offers no transitions for terminal states", () => {
    expect(ALLOWED_TRANSITIONS.completed).toEqual([]);
    expect(ALLOWED_TRANSITIONS.cancelled).toEqual([]);
  });

  it("offers complete + cancel while in progress", () => {
    expect(ALLOWED_TRANSITIONS.in_progress).toEqual(["complete", "cancel"]);
  });
});
