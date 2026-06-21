import { expect, type Page } from "@playwright/test";

/**
 * Helpers for driving the Keycloak (Authorization Code + PKCE) login flow from
 * the app's UI.
 *
 * The flow is: the app's "Sign in" button calls `signinRedirect()`, which sends
 * the browser to Keycloak's hosted login page; the user submits credentials;
 * Keycloak redirects back to `/auth/callback`, which forwards home once the
 * session is established. We anchor the "logged in" assertion on the app's
 * "Sign out" control (rendered by `AuthControls` only when authenticated)
 * rather than on a URL, since the callback rewrites the URL itself.
 *
 * Seeded credentials (see infrastructure/keycloak/nextup-realm.json) follow the
 * pattern `<username>` / `<username>pass`, e.g. `player1` / `player1pass`.
 */

/** Seeded usernames, for type-safe call sites. */
export type SeededUser =
  | "player1"
  | "player2"
  | "player3"
  | "organizer1"
  | "admin1";

/** The password for a seeded user is always `<username>pass`. */
export function passwordFor(username: SeededUser): string {
  return `${username}pass`;
}

/**
 * Log in as a seeded user, starting from the app home page and finishing back
 * in the app with an authenticated session.
 */
export async function loginAs(
  page: Page,
  username: SeededUser,
  password: string = passwordFor(username),
): Promise<void> {
  await page.goto("/");

  // `AuthControls` renders a brief "…" placeholder while the OIDC session is
  // loading; wait for the real "Sign in" button before clicking it.
  const signIn = page.getByRole("button", { name: "Sign in" });
  await signIn.waitFor({ state: "visible" });
  await signIn.click();

  // We are now on the Keycloak hosted login page. The default Keycloak theme
  // uses these stable ids for the username/password form.
  await page.waitForSelector("#username");
  await page.fill("#username", username);
  await page.fill("#password", password);
  await page.click("#kc-login");

  // Back in the app: the "Sign out" control only appears once authenticated.
  await expect(page.getByRole("button", { name: "Sign out" })).toBeVisible();
}
