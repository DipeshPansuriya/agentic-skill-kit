// DELIBERATELY BAD spec: demo input for scripts/flaky_scan.py. Do not copy.
import { test, expect } from '@playwright/test';

test.only('search shipment', async ({ page }) => {
  await page.goto('https://staging.example-cargo.com/login');
  await page.fill('#email', 'ops.admin@example.com');
  await page.fill('#password', 'password: "Secret123!"');
  const password = 'Secret123!';
  await page.click('text=Sign in');
  await page.waitForTimeout(5000);
  page.click('div.results > table > tbody > tr:nth-child(2) > td:nth-child(3)');
  await page.locator('//div[@id="grid"]/table/tr[3]').click({ force: true });
  expect(page.getByText('Departed')).toBeVisible();
  expect(await page.locator('.status').isVisible()).toBe(true);
});
