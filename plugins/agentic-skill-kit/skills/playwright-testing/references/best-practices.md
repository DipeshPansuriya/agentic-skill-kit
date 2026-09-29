# Playwright Best Practices (TypeScript, `@playwright/test`)

## Locators
Priority: what a user or assistive tech perceives.

| Prefer | Example | Notes |
|---|---|---|
| `getByRole` | `page.getByRole('button', { name: 'Search' })` | Most resilient; also checks accessibility. `exact: true` for exact name |
| `getByLabel` | `page.getByLabel('AWB number')` | Form fields with `<label>` or `aria-label` |
| `getByPlaceholder` / `getByText` | `page.getByText('Shipment not found')` | Text for non-interactive content |
| `getByTestId` | `page.getByTestId('uld-grid')` | Stable contract when no accessible name; configure `testIdAttribute` if not `data-testid` |
| CSS (last resort) | `page.locator('#awb-results')` | Never XPath, never `nth-child`/deep DOM chains |

- Narrow with chaining and filters: `page.getByRole('row').filter({ hasText: '176-12345675' }).getByRole('button', { name: 'Track' })`.
- Locators are lazy and strict: an action on a locator matching 2+ elements throws. Fix by making it specific, not with `.first()` (use `.first()`/`.nth()` only when order is the thing under test).
- Generate candidates with `npx playwright codegen <url>` or the VS Code extension "Pick locator", then clean up.
- ARIA snapshot assertions (`await expect(locator).toMatchAriaSnapshot(...)`) check structure of a region without brittle selectors.

## Web-first assertions and auto-waiting
- Actions (`click`, `fill`, ...) auto-wait for the element to be attached, visible, stable, enabled and receiving events.
- Assertions retry until timeout (default 5 s, `expect.timeout` in config):
  `await expect(page.getByRole('status')).toHaveText('Departed')`, `toBeVisible`, `toHaveURL`, `toHaveCount`, `toHaveValue`, `toBeEnabled`.
- Anti-patterns: `expect(await locator.isVisible()).toBe(true)` (no retry); `expect(await locator.textContent()).toBe(...)` (no retry); `page.waitForTimeout(3000)`.
- Wait for a network event when that is the behaviour: `const resp = page.waitForResponse('**/api/shipments*'); await btn.click(); await resp;`.
- Custom polling: `await expect.poll(() => api.getStatus(awb)).toBe('DEP')`; block retry: `await expect(async () => { ... }).toPass()`.
- Soft assertions for multi-field checks: `expect.soft(...)`.
- Negative assertions retry too: `await expect(spinner).toBeHidden()`.

## Test isolation
- Each test gets a fresh `BrowserContext` (cookies, storage): don't share pages between tests.
- Own your data: create via API in `beforeEach`/fixture; unique names (`AUTO-${testInfo.workerIndex}-${Date.now()}`); clean up in fixture teardown (or rely on a disposable env).
- No `test.describe.serial` unless the flow truly is one scenario; prefer one longer test with `test.step()`.
- `fullyParallel: true` exposes hidden coupling early.

## Fixtures
```ts
import { test as base, expect } from '@playwright/test';
import { ShipmentSearchPage } from './pages/shipment-search.page';

type Fixtures = { searchPage: ShipmentSearchPage; seededAwb: string };

export const test = base.extend<Fixtures>({
  searchPage: async ({ page }, use) => {
    await use(new ShipmentSearchPage(page));
  },
  seededAwb: async ({ request }, use) => {
    const res = await request.post('/api/test-data/shipments', { data: { origin: 'DXB', destination: 'LHR' } });
    expect(res.ok()).toBeTruthy();
    const { awbNumber } = await res.json();
    await use(awbNumber);
    await request.delete(`/api/test-data/shipments/${awbNumber}`);   // teardown
  },
});
export { expect };
```
- Fixtures are lazy (only set up if the test uses them), composable, and support `{ scope: 'worker' }` for expensive shared setup and `{ auto: true }`.
- Put built-in `expect` extensions (`expect.extend`) and shared fixtures in one `fixtures.ts`.

## Page Object Model vs fixtures
| | Page objects | Fixtures |
|---|---|---|
| Purpose | Encapsulate locators + user actions of a page/component | Provide ready objects/state to tests |
| Use | Screens used by many tests (search, booking form) | Setup/teardown, data, auth, wiring POs |
| Keep them | Thin: locators as readonly fields, methods named after user intent (`searchByAwb`), no assertions except reusable "expectLoaded" | Small and composable |

Best combination: page objects **exposed through fixtures** (see `templates/page-object.ts`). Avoid deep inheritance hierarchies and "god" page objects.

## Authentication via storageState
- A `setup` project logs in once and saves state; browser projects depend on it:
```ts
// auth.setup.ts
import { test as setup, expect } from '@playwright/test';
const authFile = 'playwright/.auth/user.json';
setup('authenticate', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Email').fill(process.env.E2E_USER!);
  await page.getByLabel('Password').fill(process.env.E2E_PASSWORD!);
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
  await page.context().storageState({ path: authFile });
});
```
- Or authenticate via API (`request.post('/api/login')` then `request.storageState({ path })`), faster.
- Multiple roles: one file per role; `test.use({ storageState: 'playwright/.auth/agent.json' })`.
- Tests that change server-side user state (password, settings): use a per-worker account (worker-scoped fixture).
- Add `playwright/.auth` to `.gitignore`. Session storage is not saved: set it via `addInitScript` if the app needs it.

## API setup via request context
- `request` fixture shares `baseURL` and `extraHTTPHeaders` from config; `page.request` shares the page's cookies.
- Seed data and verify back-end effects via API; use the UI only for the behaviour being tested.
- Standalone API tests are fine in Playwright (`request.get(...)` + `expect(response).toBeOK()`).

## Network mocking
```ts
await page.route('**/api/flights/EK203*', route =>
  route.fulfill({ status: 200, json: { flight: 'EK203', status: 'DELAYED', etd: '2026-09-27T14:05:00Z' } }));
await page.route('**/*.{png,jpg}', route => route.abort());            // speed up
await page.route('**/api/rates', async route => {                        // modify real response
  const response = await route.fetch();
  const json = await response.json();
  await route.fulfill({ response, json: { ...json, currency: 'USD' } });
});
```
- Register routes **before** the navigation/action that triggers the request.
- Record/replay: `page.routeFromHAR('hars/flights.har', { url: '**/api/**', update: false })`.
- Mock third parties (payment, maps, carrier APIs) and error paths (500, timeouts) you cannot trigger for real. Don't mock your own backend in true E2E tests.
- Time: `await page.clock.install({ time: new Date('2026-09-27T08:00:00Z') })`, then `page.clock.fastForward('02:00')` for cut-off/countdown logic.
- WebSockets: `page.routeWebSocket()` (1.48+).

## Parallelism and sharding
- `fullyParallel: true` runs tests within files in parallel; `workers` limits processes (CI: 1–4 per runner depending on CPU/app capacity, or `'50%'`).
- Shard across machines: `npx playwright test --shard=1/4`; combine with `reporter: 'blob'` and `npx playwright merge-reports --reporter html ./all-blob-reports`.
- Tests needing exclusive resources: tag and run in a separate project with `workers: 1`, or `test.describe.configure({ mode: 'serial' })` for that file only.

## Retries and trace viewer
- `retries: process.env.CI ? 2 : 0`; results show **flaky** for pass-on-retry. `failOnFlakyTests: true` can fail the run on any flake.
- `trace: 'on-first-retry'` (or `'retain-on-failure'`); open with `npx playwright show-trace trace.zip` or trace.playwright.dev: timeline, DOM snapshots before/after each action, network, console, source.
- Also `screenshot: 'only-on-failure'`, `video: 'retain-on-failure'`.
- Debug locally: `npx playwright test --ui`, `--debug`, `await page.pause()`, `--last-failed`, `--only-changed`.

## Visual comparisons
- `await expect(page).toHaveScreenshot('awb-detail.png', { mask: [page.getByTestId('timestamp')], maxDiffPixelRatio: 0.01 })`.
- Baselines are OS/browser/font specific: generate and compare in the same environment (the CI Docker image `mcr.microsoft.com/playwright:v<version>-noble`); update with `--update-snapshots`.
- Mask or freeze dynamic content (dates, ads, animations: `animations: 'disabled'` is default for screenshots), stable viewport, `page.clock` for time.
- Keep visual tests few and focused on components/pages where layout matters.

## Flaky test diagnosis
| Symptom | Likely cause | Fix |
|---|---|---|
| Passes alone, fails in suite | Shared data or order dependency | Unique data per test; fixture teardown; remove serial coupling |
| Fails only in CI | Slower machine, different viewport/timezone/locale, missing env var, too many workers | Set `timezoneId`, `locale`, viewport in config; reduce workers; check env |
| "strict mode violation" | Locator matches several elements | More specific locator / filter |
| Element not found intermittently | Assertion without await; checking before data loads; `isVisible()` snapshot | Web-first assertion on the final state |
| Click does nothing | Clicked before hydration / handler attached; overlay | Assert the ready state first (e.g. enabled button, loaded heading); never `force: true` |
| Wrong data | Race with background refresh / polling | Wait for the response or final text; mock the refresh |
| Time-dependent failures | Real clock, midnight/UTC offset, cut-off time | `page.clock`, fixed `timezoneId` |
| Visual diffs | Fonts/OS, animation, dynamic content | Same Docker image; mask; disable animations |

Process: reproduce with `--repeat-each=20 --workers=<CI value>`; read the trace of a failing run; fix the cause; re-run repeat to confirm; run `scripts/flaky_scan.py`.

## Organisation
- `tests/` by feature (`tests/tracking/awb-search.spec.ts`), `pages/` for page objects, `fixtures.ts`, `auth.setup.ts`.
- Tags in titles or `{ tag: '@smoke' }`; run with `--grep @smoke`.
- `test.step('Search AWB', async () => {...})` for readable reports.
- Keep each test focused on one behaviour; aim for < 30 s per test.
