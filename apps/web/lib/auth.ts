/**
 * OIDC client configuration (Keycloak, Authorization Code + PKCE).
 *
 * The settings reference `window` (for redirect URIs), so this MUST run only on
 * the client. `getAuthConfig` is a function — never a top-level const — so the
 * `window` access happens at render time, not when the module is imported during
 * SSR/prerender (which would crash `next build`).
 */
import type { AuthProviderProps } from "react-oidc-context";

import { env } from "@/lib/env";

/** Build `react-oidc-context` provider settings from public config + `window`. */
export function getAuthConfig(): AuthProviderProps {
  return {
    authority: env.oidcIssuer,
    client_id: env.oidcClientId,
    redirect_uri: `${window.location.origin}/auth/callback`,
    post_logout_redirect_uri: window.location.origin,
    response_type: "code",
    scope: "openid profile email",
    automaticSilentRenew: false,
  };
}

/** Strip the `?code=…&state=…` callback params after a successful sign-in. */
export function onSigninCallback(): void {
  window.history.replaceState({}, document.title, window.location.pathname);
}
