import { expect, test } from "@playwright/test";

import { loginAs } from "./helpers/auth";

/**
 * Scenario 3 (spec §19): organizer check-in.
 *
 * organizer1 opens a run's roster (`/runs/{id}/roster`), checks in a confirmed
 * player, and the roster shows the checked-in state.
 *
 * We check in player2 (display name "Pablo Player"), who is seeded as confirmed
 * on "Sold-out Saturday" and stays confirmed regardless of Scenario 2 (which
 * only frees player1's spot and promotes player3). This keeps the scenarios
 * independent of ordering while still sharing one seeded run.
 *
 * Selectors target `RosterView` (components/RosterView.tsx): a confirmed row
 * renders the player's display name, a "Check in" button, and — once checked in
 * — the text "Checked in ✓".
 *
 * Requires the live stack (`make up`) and a fresh `make seed`.
 */
test.describe("Scenario 3: organizer check-in", () => {
  test("organizer checks in a confirmed player and the roster shows checked-in", async ({
    page,
  }) => {
    await loginAs(page, "organizer1");

    // Open the run, then follow the organizer-only "Roster" link.
    await page.goto("/runs");
    await page.getByRole("link", { name: "Sold-out Saturday" }).click();
    await expect(
      page.getByRole("heading", { name: "Sold-out Saturday" }),
    ).toBeVisible();
    await page.getByRole("link", { name: "Roster" }).click();

    // The roster page heading.
    await expect(
      page.getByRole("heading", { name: "Roster" }),
    ).toBeVisible();

    // Locate Pablo Player's confirmed row and check him in.
    const row = page.getByRole("listitem").filter({ hasText: "Pablo Player" });
    await expect(row).toBeVisible();
    await row.getByRole("button", { name: "Check in" }).click();

    // The row now shows the checked-in state instead of the action buttons.
    await expect(row.getByText(/checked in/i)).toBeVisible();
  });
});
