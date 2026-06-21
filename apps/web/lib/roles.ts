/**
 * UX-only role extraction from an OIDC access token.
 *
 * The backend is the real authority; these roles only drive what the UI offers
 * (e.g. showing an organizer dashboard link). The JWT signature is NOT verified
 * here — never gate anything security-relevant on this.
 */

/** Roles the UI knows how to react to. */
export const KNOWN_ROLES = ["player", "organizer", "admin"] as const;
export type KnownRole = (typeof KNOWN_ROLES)[number];

const KNOWN_ROLE_SET = new Set<string>(KNOWN_ROLES);

/** Decode a base64url-encoded JWT segment to a UTF-8 string (browser-safe). */
function decodeBase64Url(segment: string): string {
  const base64 = segment.replace(/-/g, "+").replace(/_/g, "/");
  const padded = base64.padEnd(Math.ceil(base64.length / 4) * 4, "=");
  return atob(padded);
}

/**
 * Returns the Keycloak realm roles in the token, intersected with the roles the
 * UI understands. Any malformed/empty token decodes to `[]` rather than throwing.
 */
export function rolesFromAccessToken(
  token: string | null | undefined,
): KnownRole[] {
  if (!token) return [];

  const payloadSegment = token.split(".")[1];
  if (!payloadSegment) return [];

  try {
    const payload: unknown = JSON.parse(decodeBase64Url(payloadSegment));
    if (typeof payload !== "object" || payload === null) return [];

    const realmAccess = (payload as { realm_access?: unknown }).realm_access;
    if (typeof realmAccess !== "object" || realmAccess === null) return [];

    const roles = (realmAccess as { roles?: unknown }).roles;
    if (!Array.isArray(roles)) return [];

    return roles.filter(
      (role): role is KnownRole =>
        typeof role === "string" && KNOWN_ROLE_SET.has(role),
    );
  } catch {
    return [];
  }
}
