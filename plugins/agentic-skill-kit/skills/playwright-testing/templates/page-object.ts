import { type Locator, type Page, expect } from '@playwright/test';

/**
 * Page object for the shipment search screen (template; replace names with your app's
 * accessible names). Locators are readonly fields; methods are named after user intent.
 * Save as pages/shipment-search.page.ts and expose it through a fixture (see example.spec.ts).
 */
export class ShipmentSearchPage {
  readonly page: Page;
  readonly heading: Locator;
  readonly awbInput: Locator;
  readonly originInput: Locator;
  readonly searchButton: Locator;
  readonly results: Locator;
  readonly emptyState: Locator;

  constructor(page: Page) {
    this.page = page;
    this.heading = page.getByRole('heading', { name: 'Shipment search' });
    this.awbInput = page.getByLabel('AWB number');
    this.originInput = page.getByLabel('Origin');
    this.searchButton = page.getByRole('button', { name: 'Search' });
    this.results = page.getByRole('table', { name: 'Search results' });
    this.emptyState = page.getByText('No shipments found');
  }

  async goto(): Promise<void> {
    await this.page.goto('/shipments/search');
    await expect(this.heading).toBeVisible();
  }

  async searchByAwb(awbNumber: string): Promise<void> {
    await this.awbInput.fill(awbNumber);
    await this.searchButton.click();
  }

  async searchByOrigin(iataCode: string): Promise<void> {
    await this.originInput.fill(iataCode);
    await this.searchButton.click();
  }

  /** Row for one AWB; assertions stay in the test. */
  rowFor(awbNumber: string): Locator {
    return this.results.getByRole('row').filter({ hasText: awbNumber });
  }
}
