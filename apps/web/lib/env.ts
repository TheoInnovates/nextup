/**
 * Typed access to public (browser-exposed) configuration.
 *
 * `NEXT_PUBLIC_*` values are inlined at build time. The default targets the
 * Docker Compose stack host so the app works out of the box locally.
 */
export const env = {
  apiBaseUrl:
    process.env.NEXT_PUBLIC_API_URL ?? "https://api.nextup.local/api/v1",
  oidcIssuer:
    process.env.NEXT_PUBLIC_OIDC_ISSUER ??
    "https://auth.nextup.local/realms/nextup",
  oidcClientId: process.env.NEXT_PUBLIC_OIDC_CLIENT_ID ?? "nextup-web",
} as const;
