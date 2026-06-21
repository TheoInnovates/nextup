import { expect, test } from "@playwright/test";

import { loginAs } from "./helpers/auth";

/**
 * Scenario 2 (spec §19): waitlist promotion + notification.
 *
 * The seeded full run "Sold-out Saturday" (capacity 2) has player1 + player2
 * CONFIRMED and player3 WAITLISTED at #1. When a confirmed player frees their
 * spot, the backend's `_cancel_and_promote` promotes the earliest waitlister and
 * emits a `waitlist_promoted` notification (title "You're in!", message
 * "A spot opened up — you're confirmed for {run title}.").
 *
 * We drive the cancellation through the UI that actually exists: a player can
 * cancel their OWN registration from the run detail page (`RegistrationPanel`).
 * The roster has no per-registration cancel control, so the organizer path the
 * spec mentions is intentionally NOT used here.
 *
 * Steps:
 *   1. player3 logs in and confirms they're WAITLISTED on "Sold-out Saturday"
 *      (the seeded precondition).
 *   2. player1 logs in, opens "Sold-out Saturday", cancels their registration
 *      (this triggers promotion of player3).
 *   3. player3 logs back in and sees a CONFIRMED status for the same run plus a
 *      `waitlist_promoted` notification on /notifications.
 *
 * This scenario MUTATES seeded state (player1's registration), so it assumes a
 * fresh `make seed` and runs serially with the other specs (see
 * playwright.config.ts: workers=1, fullyParallel=false).
 *
 * Text is matched case-insensitively / by substring because the components
 * escape the apostrophe while the backend message uses a straight quote and an
 * em-dash.
 */
test.describe("Scenario 2: waitlist promotion + notification", () => {
  test("cancelling a confirmed spot promotes the waitlisted player and notifies them", async ({
    page,
  }) => {
    // --- precondition: player3 is waitlisted on the full run ----------------
    await loginAs(page, "player3");
    await page.goto("/runs");
    await page.getByRole("link", { name: "Sold-out Saturday" }).click();
    await expect(
      page.getByRole("heading", { name: "Sold-out Saturday" }),
    ).toBeVisible();
    await expect(page.getByText(/you're on the waitlist/i)).toBeVisible();
    await page.getByRole("button", { name: "Sign out" }).click();

    // --- player1 cancels their confirmed registration -----------------------
    await loginAs(page, "player1");

    await page.goto("/runs");
    await page.getByRole("link", { name: "Sold-out Saturday" }).click();
    await expect(
      page.getByRole("heading", { name: "Sold-out Saturday" }),
    ).toBeVisible();

    // player1 is seeded as confirmed, so the confirmed card + cancel control show.
    await expect(page.getByText(/you're confirmed/i)).toBeVisible();

    // Cancelling pops a window.confirm(); auto-accept it before clicking.
    page.on("dialog", (dialog) => dialog.accept());
    await page
      .getByRole("button", { name: "Cancel registration" })
      .click();

    // After cancellation the register CTA returns (no active registration).
    await expect(
      page.getByRole("button", { name: "Register for this run" }),
    ).toBeVisible();

    // Sign out before logging in as the promoted player.
    await page.getByRole("button", { name: "Sign out" }).click();

    // --- player3 (the promoted waitlister) is now confirmed + notified ------
    await loginAs(page, "player3");

    await page.goto("/runs");
    await page.getByRole("link", { name: "Sold-out Saturday" }).click();
    await expect(
      page.getByRole("heading", { name: "Sold-out Saturday" }),
    ).toBeVisible();

    // player3 was waitlisted #1 and should now be confirmed.
    await expect(page.getByText(/you're confirmed/i)).toBeVisible();

    // The promotion notification appears in the inbox.
    await page.goto("/notifications");
    await expect(
      page.getByRole("heading", { name: "Notifications" }),
    ).toBeVisible();
    await expect(page.getByText(/you're in!/i)).toBeVisible();
    await expect(page.getByText(/a spot opened up/i)).toBeVisible();
  });
});
