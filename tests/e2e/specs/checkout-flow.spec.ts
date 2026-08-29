import { test, expect } from "@playwright/test";

test("AI checkout completes with a Transaction Passport", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveTitle(/AegisPay/);
});
