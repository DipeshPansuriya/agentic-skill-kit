import { test as base, expect } from '@playwright/test';
import { ShipmentSearchPage } from './page-object';

/**
 * Example spec: login + shipment search (fake data).
 * Auth for the search tests comes from storageState written by the "setup" project
 * (see playwright.config.ts); the login test opts out to exercise the real form.
 * Test data is created through the API per test, so tests run in any order and in parallel.
 */
type Fixtures = { searchPage: ShipmentSearchPage; seededAwb: string };

const test = base.extend<Fixtures>({
  searchPage: async ({ page }, use) => {
    await use(new ShipmentSearchPage(page));
  },
  seededAwb: async ({ request }, use, testInfo) => {
    const response = await request.post('/api/test-data/shipments', {
      data: {
        reference: `E2E-${testInfo.workerIndex}-${Date.now()}`,
        origin: 'DXB',
        destination: 'LHR',
        pieces: 3,
        weightKg: 412.5,
        status: 'DEP',
      },
    });
    expect(response.ok()).toBeTruthy();
    const { awbNumber } = (await response.json()) as { awbNumber: string };
    await use(awbNumber);
    await request.delete(`/api/test-data/shipments/${awbNumber}`);
  },
});

test.describe('login', () => {
  test.use({ storageState: { cookies: [], origins: [] } });

  test('valid user reaches the dashboard', async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel('Email').fill(process.env.E2E_USER ?? '');
    await page.getByLabel('Password').fill(process.env.E2E_PASSWORD ?? '');
    await page.getByRole('button', { name: 'Sign in' }).click();

    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
  });

  test('wrong password shows an error and stays on login', async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel('Email').fill('test.user@example.com');
    await page.getByLabel('Password').fill('not-the-password');
    await page.getByRole('button', { name: 'Sign in' }).click();

    await expect(page.getByRole('alert')).toHaveText(/invalid email or password/i);
    await expect(page).toHaveURL(/\/login/);
  });
});

test.describe('shipment search', { tag: '@smoke' }, () => {
  test('finds a shipment by AWB and shows its status', async ({ searchPage, seededAwb }) => {
    await searchPage.goto();

    await test.step('search by AWB', async () => {
      await searchPage.searchByAwb(seededAwb);
    });

    const row = searchPage.rowFor(seededAwb);
    await expect(row).toBeVisible();
    await expect(row.getByRole('cell', { name: 'DXB' })).toBeVisible();
    await expect(row.getByRole('cell', { name: 'LHR' })).toBeVisible();
    await expect(row.getByRole('cell', { name: 'Departed' })).toBeVisible();
  });

  test('unknown AWB shows the empty state', async ({ searchPage }) => {
    await searchPage.goto();
    await searchPage.searchByAwb('999-00000000');

    await expect(searchPage.emptyState).toBeVisible();
  });

  test('shows a friendly error when the search API fails', async ({ page, searchPage }) => {
    await page.route('**/api/shipments/search**', (route) =>
      route.fulfill({ status: 503, json: { error: 'Service unavailable' } }),
    );
    await searchPage.goto();
    await searchPage.searchByAwb('176-12345675');

    await expect(page.getByRole('alert')).toContainText('Search is temporarily unavailable');
  });
});
