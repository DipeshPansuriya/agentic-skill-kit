---
name: playwright-testing
description: Write, fix or de-flake Playwright end-to-end tests and return runnable specs, page objects and config. Use when the user asks for a Playwright test, E2E or UI test, flaky test fix, locators, or Playwright CI in TypeScript, Python, .NET or Java.
---

# Playwright Testing

Write E2E tests like a senior SDET on an air-cargo web platform (booking, AWB tracking, shipment search, ULD screens): independent, deterministic, asserting what the user sees.

## Inputs
- A user flow or acceptance criteria ("login, search AWB 176-12345675, see status Departed")
- Existing spec files, page objects, `playwright.config.*`, failing test output, trace (`trace.zip`), CI logs
- Optional: HTML snippet / accessibility tree of the page, test data, API endpoints for setup

When given a failing test, read the error, the trace or screenshot, and the spec before changing anything.

## Defaults (ask vs assume)
| Setting | Default if not stated | Ask only if |
|---|---|---|
| Language | TypeScript with `@playwright/test` | Repo shows Python/.NET/Java; then follow `references/other-bindings.md` |
| Version | Latest stable Playwright (1.6x; templates checked against 1.63) | A feature you use is version-gated and the repo pins an old version |
| Browsers | Chromium in PR runs; Chromium + Firefox + WebKit nightly | Never |
| Base URL / creds | `process.env.BASE_URL`, `process.env.E2E_USER` / `E2E_PASSWORD` | Never; never hard-code |
| Auth | `setup` project writes `storageState`; tests reuse it | App uses per-test roles; then one state file per role |
| Structure | Fixtures + light page objects | Repo already uses another pattern; follow it |

State the defaults used in one line above the code.

## Routing
| Task | Read / use |
|---|---|
| Locators, assertions, waiting, isolation, fixtures, POM, auth, API setup, mocking, parallelism, retries, traces, visual tests, flaky diagnosis | `references/best-practices.md` |
| Python, .NET (NUnit/MSTest/xUnit) or Java bindings | `references/other-bindings.md` |
| GitHub Actions, Azure DevOps, reports, artifacts, sharding in CI | `references/ci.md` |
| New project config | `templates/playwright.config.ts` |
| New spec | `templates/example.spec.ts` |
| Page object | `templates/page-object.ts` |
| Scan tests for flakiness smells | `scripts/flaky_scan.py` (demo input: `templates/bad-example.spec.ts`) |

## Steps
1. Identify the task (new test · fix failing test · de-flake · refactor · CI) and the binding; load the matching reference.
2. Write the scenario as Given / When / Then with the **user-visible** outcome for each Then.
3. Choose locators in this order: `getByRole` (with `name`) → `getByLabel` → `getByPlaceholder` / `getByText` → `getByTestId` → CSS as a last resort (never XPath or `nth-child` chains).
4. Set up state via API (`request` fixture) or `storageState`, not through the UI, unless the UI flow is what is under test.
5. Write the test with web-first assertions (`await expect(locator).toHaveText(...)`); no `waitForTimeout`, no manual `isVisible()` polling.
6. Mock only third-party or non-deterministic dependencies with `page.route`; keep the app's own backend real in E2E unless the user says otherwise.
7. For fixes and de-flaking: reproduce with `npx playwright test <file> --repeat-each=20 --workers=4` (or `--retries=0`), open the trace (`npx playwright show-trace`), find the root cause per `references/best-practices.md`, fix the cause (not by adding waits or retries).
8. Run `python3 scripts/flaky_scan.py <tests-dir>` on the result and resolve every ERROR.
9. Give the run command, and for CI changes the pipeline YAML from `references/ci.md`.
10. Run the self-check and fix before returning.

## Rules
- Tests are independent: no order dependency, no shared mutable data; each test creates or uniquely names its data (e.g. suffix with `testInfo.workerIndex` + timestamp).
- Deterministic: no `waitForTimeout` / `sleep`; control time with `page.clock`, randomness with fixed seeds, and external APIs with `page.route`.
- Assert user-visible outcomes (text, role, URL, visible state), not implementation details (CSS classes, internal state, console).
- Prefer role-based locators; add `data-testid` to the app only when no accessible name exists, and say so.
- Never hard-code secrets, tokens, or environment URLs; use env vars / CI secrets and `baseURL`.
- Never commit `test.only`; never use `{ force: true }` to hide an actionability problem; fix the cause.
- Keep `storageState` files and traces with real data out of git (`.gitignore` `playwright/.auth/`).
- Retries are a safety net that reports flakes, not a fix; a test passing only on retry is a bug to fix.
- Use clearly fake test data (AWB `176-12345675`, `test.user@example.com`).
- Never invent app selectors or text: if the DOM is not given, write role/name locators from the stated UI text and mark them **Verify**.

## Self-check
- [ ] Code compiles for the binding (imports, `async`/`await`, types)
- [ ] Every `expect` on a locator/page is awaited and web-first; no `waitForTimeout`, `test.only`, `force: true`
- [ ] Locators are role/label/testid based; no XPath or positional CSS
- [ ] Each test runs alone and in parallel (`fullyParallel`) with its own data
- [ ] No secrets or hard-coded environment URLs
- [ ] Assertions check what the user sees
- [ ] `scripts/flaky_scan.py` reports 0 errors on the new/changed files

## Output
Return: defaults line → files (path + full code in fenced blocks) → how to run (`npx playwright test ...`) → what each test proves (one line each) → for fixes, root cause + why the fix is deterministic → **Verify** items (assumed selectors/text).

Test cases for this skill: `evals/test-cases.md` (rerun after every edit).
