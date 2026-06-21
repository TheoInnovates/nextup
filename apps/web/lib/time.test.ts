import { describe, expect, it } from "vitest";

import { formatInTimeZone, isoToLocalInput } from "@/lib/time";

// A summer (DST) instant so the expected wall-clock hours are unambiguous:
// 2026-06-23 18:00Z is 14:00 EDT (New York) and 11:00 PDT (Los Angeles).
const SUMMER_18Z = "2026-06-23T18:00:00Z";

describe("formatInTimeZone", () => {
  it("renders a UTC instant in the given IANA zone (New York, summer)", () => {
    const out = formatInTimeZone(SUMMER_18Z, "America/New_York", {
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    });
    // ICU may use a narrow no-break space before AM/PM, so match loosely.
    expect(out).toMatch(/2:00.*PM/);
  });

  it("renders the same instant differently in Los Angeles", () => {
    const out = formatInTimeZone(SUMMER_18Z, "America/Los_Angeles", {
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    });
    expect(out).toMatch(/11:00.*AM/);
  });

  it("produces different output for two zones at the same instant", () => {
    const ny = formatInTimeZone(SUMMER_18Z, "America/New_York");
    const la = formatInTimeZone(SUMMER_18Z, "America/Los_Angeles");
    expect(ny).not.toEqual(la);
  });

  it("returns the original string for an unparseable input", () => {
    expect(formatInTimeZone("not-a-date", "America/New_York")).toBe("not-a-date");
  });
});

describe("isoToLocalInput", () => {
  it("formats to a datetime-local-shaped string", () => {
    expect(isoToLocalInput(SUMMER_18Z)).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/);
  });

  it("returns an empty string for an unparseable input", () => {
    expect(isoToLocalInput("nope")).toBe("");
  });
});
