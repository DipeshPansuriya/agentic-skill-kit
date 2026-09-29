# Playwright Automation Hand-off (optional)

Add this block only when the user asks for automation hints.

## Pick candidates
| Automate | Keep manual |
|---|---|
| High-priority positive + regression paths | One-off UAT, visual judgement |
| Data-driven boundary sets | Tests needing physical devices/scanners |
| Stable UI with test IDs | Flows behind CAPTCHA/OTP without test bypass |

## Hand-off table
| TC ID | Automate? | Page / API | Locator hints (data-testid) | Data source | Notes |
|---|---|---|---|---|---|
| TC-EDO-001 | Yes | /import/edo | `edo-awb-input`, `edo-issue-btn` | fixtures/awbs.json | Needs paid-charges fixture |

## Skeleton (one test per TC ID)
```ts
import { test, expect } from '@playwright/test';

test('TC-EDO-001 Issue e-DO when charges paid', async ({ page }) => {
  await page.goto('/import/edo');
  await page.getByTestId('edo-awb-input').fill('000-00000000');
  await page.getByTestId('edo-issue-btn').click();
  await expect(page.getByTestId('edo-number')).toBeVisible();
});
```
- Name tests with the TC ID so results trace back.
- Use `test.describe.parallel` per module; use fixtures for test data, never production AWBs.
