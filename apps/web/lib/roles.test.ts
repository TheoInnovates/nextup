import { describe, expect, it } from "vitest";

import { rolesFromAccessToken } from "@/lib/roles";

/** Symmetric base64url encoder mirroring the decoder in `lib/roles.ts`. */
function base64UrlEncode(value: string): string {
  return btoa(value).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

/** Build a fake (unsigned) JWT with the given payload object. */
function fakeJwt(payload: unknown): string {
  const header = base64UrlEncode(JSON.stringify({ alg: "none", typ: "JWT" }));
  const body = base64UrlEncode(JSON.stringify(payload));
  return `${header}.${body}.sig`;
}

describe("rolesFromAccessToken", () => {
  it("returns known realm roles, filtering out unknown ones", () => {
    const token = fakeJwt({
      realm_access: { roles: ["organizer", "offline_access"] },
    });
    expect(rolesFromAccessToken(token)).toEqual(["organizer"]);
  });

  it("returns multiple known roles", () => {
    const token = fakeJwt({
      realm_access: { roles: ["player", "admin", "uma_authorization"] },
    });
    expect(rolesFromAccessToken(token)).toEqual(["player", "admin"]);
  });

  it("returns [] when realm_access is missing", () => {
    expect(rolesFromAccessToken(fakeJwt({ sub: "abc" }))).toEqual([]);
  });

  it("returns [] for null/undefined/empty tokens", () => {
    expect(rolesFromAccessToken(null)).toEqual([]);
    expect(rolesFromAccessToken(undefined)).toEqual([]);
    expect(rolesFromAccessToken("")).toEqual([]);
  });

  it("returns [] for a malformed token", () => {
    expect(rolesFromAccessToken("not-a-jwt")).toEqual([]);
    expect(rolesFromAccessToken("a.b")).toEqual([]);
    expect(rolesFromAccessToken("a.%%%.c")).toEqual([]);
  });
});
