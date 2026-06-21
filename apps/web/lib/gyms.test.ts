import { describe, expect, it } from "vitest";

import {
  courtSchema,
  gymCreateSchema,
  gymPageSchema,
  gymSchema,
} from "@/lib/gyms";

const validGym = {
  id: "11111111-1111-1111-1111-111111111111",
  name: "Downtown Rec",
  description: "Two full courts",
  address_line_1: "100 Main St",
  address_line_2: null,
  city: "Brooklyn",
  state: "NY",
  postal_code: "11201",
  timezone: "America/New_York",
  owner_user_id: "22222222-2222-2222-2222-222222222222",
  is_active: true,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

describe("gymSchema", () => {
  it("parses a valid gym", () => {
    expect(() => gymSchema.parse(validGym)).not.toThrow();
  });

  it("fails when a required field is missing", () => {
    const { name: _omitted, ...withoutName } = validGym;
    void _omitted;
    expect(gymSchema.safeParse(withoutName).success).toBe(false);
  });

  it("accepts a null address_line_2", () => {
    expect(gymSchema.parse(validGym).address_line_2).toBeNull();
  });
});

describe("courtSchema", () => {
  it("parses a valid court", () => {
    const court = {
      id: "33333333-3333-3333-3333-333333333333",
      gym_id: validGym.id,
      name: "Court A",
      is_active: true,
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
    };
    expect(() => courtSchema.parse(court)).not.toThrow();
  });
});

describe("gymPageSchema", () => {
  it("parses a paginated envelope", () => {
    const page = { items: [validGym], total: 1, limit: 50, offset: 0 };
    expect(gymPageSchema.parse(page).items).toHaveLength(1);
  });

  it("parses an empty envelope", () => {
    const page = { items: [], total: 0, limit: 50, offset: 0 };
    expect(gymPageSchema.parse(page).items).toHaveLength(0);
  });
});

describe("gymCreateSchema", () => {
  it("rejects empty required fields with messages", () => {
    const result = gymCreateSchema.safeParse({
      name: "",
      address_line_1: "",
      city: "",
      state: "",
      postal_code: "",
      timezone: "",
    });
    expect(result.success).toBe(false);
    if (!result.success) {
      const fields = result.error.issues.map((i) => i.path[0]);
      expect(fields).toContain("name");
      expect(fields).toContain("address_line_1");
      expect(fields).toContain("city");
      expect(fields).toContain("timezone");
    }
  });

  it("accepts a minimal valid payload (optional description omitted)", () => {
    const result = gymCreateSchema.safeParse({
      name: "Rec",
      address_line_1: "1 St",
      city: "NYC",
      state: "NY",
      postal_code: "10001",
      timezone: "America/New_York",
    });
    expect(result.success).toBe(true);
  });
});
