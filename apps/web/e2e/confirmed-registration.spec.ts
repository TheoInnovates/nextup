import { expect, test } from "@playwright/test";

import { loginAs } from "./helpers/auth";

/**
 * Scenario 1 (spec §19): confirmed registration.
 *
 * player1 logs in, opens the open run "Tuesday Night Run" (seeded, capacity 20),
 * registers, and sees a CONFIRMED status with an arrival time and an expected
 * play time.
 *
 * Requires the live stack (`make up`) and a fresh `make seed`. The run has
 * plenty of capacity, so this scenario does not depend on other scenarios.
 *
 * Selectors target the copy rendered by `RegistrationStatusView`
 * (components/RegistrationPanel.tsx). Text is matched case-insensitively /
 * by substring because the components escape the apostrophe (`&apos;`) while
 * sharing the same wording as the spec.
 */
test.describe("Scenario 1: confirmed registration", () => {
  test("player1 registers for an open run and is confirmed with times", async ({
    page,
  }) => {
    await loginAs(page, "player1");

    // Navigate to the runs list and open the seeded open run by its title.
    await page.goto("/runs");
    await page.getByRole("link", { name: "Tuesday Night Run" }).click();

    // The run detail page shows the run title as a heading.
    await expect(
      page.getByRole("heading", { name: "Tuesday Night Run" }),
    ).toBeVisible();

    // Register. The CTA reads "Register for this run" (RegistrationStatusView).
    await page
      .getByRole("button", { name: "Register for this run" })
      .click();

    // Confirmed status card: "You're confirmed." plus arrival + play times.
    await expect(page.getByText(/you're confirmed/i)).toBeVisible();
    await expect(page.getByText(/Arrive by:/i)).toBeVisible();
    await expect(page.getByText(/Expected to play:/i)).toBeVisible();
  });
});
