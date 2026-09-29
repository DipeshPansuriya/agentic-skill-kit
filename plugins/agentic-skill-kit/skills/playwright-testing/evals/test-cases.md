# Test Cases: playwright-testing

Rerun after every edit. Score each with the 0–5 checklist.

## Quality checklist (1 point each, 0–5)
1. Code compiles/runs for the binding (imports, awaits, types)
2. Role/label/testid locators; web-first assertions; no hard waits, `test.only`, `force: true`
3. Tests independent and deterministic (own data, mocks for third parties, fixed clock/timezone when relevant)
4. No secrets or hard-coded env URLs; nothing invented (unknown selectors marked Verify)
5. Usable as-is: file paths, run command, what each test proves

## Cases
| # | Type | Request | Should trigger? | Expected |
|---|---|---|---|---|
| 1 | Single: new test | "Write a Playwright test: login, search AWB 176-12345675, see status Departed" | Yes | TS spec with `getByLabel`/`getByRole`, `await expect(...).toHaveText`, env creds, storageState or login test; run command |
| 2 | Single: locators | "My test uses `div > table > tr:nth-child(3) td` — make it robust" | Yes | Rewritten with `getByRole('row').filter({ hasText })` + `getByRole('cell')`; explains strictness |
| 3 | Single: flaky fix | "This test fails 1 in 10 in CI" + spec with `waitForTimeout(3000)` | Yes | Root cause via trace/`--repeat-each`; waits replaced with web-first assertion or `waitForResponse`; no added retries as the fix |
| 4 | Single: auth | "Stop logging in through the UI in every test" | Yes | `auth.setup.ts` + `setup` project dependency + `storageState`; `.gitignore` note; per-role files |
| 5 | Single: mocking | "Test the error banner when the flight status API is down" | Yes | `page.route` with `route.fulfill({ status: 503 })` registered before navigation; asserts visible banner |
| 6 | Single: POM | "Refactor these specs into page objects" | Yes | Thin page objects (readonly locators, intent methods) exposed via fixtures; assertions stay in tests |
| 7 | Single: CI | "Run our Playwright suite in Azure DevOps with 4 shards and publish results" | Yes | YAML from `references/ci.md`: `parallel: 4`, `--shard`, JUnit publish, report artifact on `succeededOrFailed()`, secrets mapped |
| 8 | Single: other binding | "Write the same test in Python with pytest" | Yes | `pytest-playwright` sync API, `get_by_role`, `expect(...).to_have_text`, env vars |
| 9 | Single: .NET | "NUnit Playwright test for shipment search" | Yes | `PageTest` base, `await Expect(...).ToHaveTextAsync`, `ContextOptions()` with BaseURL; CS4014 note |
| 10 | Multi | "Write tests for booking, set up GitHub Actions with sharding and a merged HTML report" | Yes | Specs + config + workflow with blob reports and `merge-reports` |
| 11 | Edge: no DOM given | "Test the ULD build-up screen" with only a description | Yes | Role/name locators from described UI text marked **Verify**; no invented test ids; asks for DOM/URL only if needed |
| 12 | Edge: secrets in input | User pastes a spec containing a real-looking password and prod URL | Yes | Moves to env vars / CI secrets, flags them; `scripts/flaky_scan.py` output shows `hardcoded-secret`/`hardcoded-url` |
| 13 | Edge: visual | "Add screenshot tests for the AWB detail page" | Yes | `toHaveScreenshot` with masks for timestamps, run in the Playwright Docker image, `--update-snapshots` guidance |
| 14 | Near-miss | "Write manual test cases from this shipment search requirement" | **No** | Route to test-cases-from-requirements |
| 15 | Near-miss | "Write a .NET repository class and unit tests for the booking service" | **No** | Route to backend-engineering (unit tests, not browser E2E) |
| 16 | Near-miss | "Should we use microservices or a modular monolith for tracking?" | **No** | Route to software-architecture |
| 17 | Consistency | Run #1 three times | Yes | Same structure 3/3: defaults line → files → run command → what each test proves → Verify items |
