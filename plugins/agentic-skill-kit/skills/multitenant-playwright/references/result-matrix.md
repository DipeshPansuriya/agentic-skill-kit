# Result matrix and run outcomes

Files: `templates/summary.ts` (pure logic), `templates/summary-reporter.ts`, `templates/case-log.ts`, `templates/combine-results.ts`, `templates/combine-cli.ts`, `templates/check-summary.ts`.

## The reporter
- **Derives tenant and module from the project name** (`tenant__module`, `templates/project-name.ts`), so a new tenant needs no reporter change. A reviewed reporter fell back to upper-casing a code because its label table only knew two tenants; derive, do not enumerate.
- **Never throws.** Every callback is wrapped; a reporting bug must neither hide a failure nor fail a green run.
- **No-op under `--list`** and when no tenant project exists (unit-only runs).
- Records the final attempt of each test (`test.outcome()`: passed, failed, flaky, skipped).
- A passing setup is not a result: it never makes a tenant look as if it ran tests. A failing setup is a failed case for that tenant.
- Forces the run to `failed` (via `onEnd`) when an expected tenant produced nothing, even if Playwright says passed.
- Pass rate counts flaky as passed, excludes skipped, shows flaky separately.

## The matrix
Rows are scenario titles, **tenants are columns**, cells are `Pass / Fail / Flaky / Skipped / n/a` (n/a = that tenant has no such scenario or it is out of scope; show the reason from the profile). Below the rows: per-tenant totals and a status line. Output `summary.json` (machine) and `summary.md`; for email use an inline-styled table. Put per-tenant totals in the visible table, not only in JSON (a reviewed email showed counts per module while its docs promised per tenant).

## Freshness
Show how old each tenant's latest valid result is: green up to 48 h, amber older, red over 7 days or no execution (`freshness()` in `templates/combine-results.ts`; the thresholds are choices).

## Failure taxonomy
Keep outcomes apart; each has its own effect.
| Status | Meaning | Effect |
|---|---|---|
| `env-down` | environment or API tier unreachable at preflight | no results; earlier latest stands; failure |
| `no-credentials` | no usable credential (missing or placeholder) | failure, never skipped |
| `job-failed` | the tenant job died before producing results | no results; failure |
| `no-results` | the job ran but executed no test | failure |
| `mismatched` | recorded tenant differs from the expected tenant | listed, never applied |
| `incomplete` | no `end` line (killed run) | finished cases still count |
| `failed` / `passed` | normal outcomes; flaky counted separately | |

## Kill-resilient, append-only case log
One JSON line per event, appended the moment a test ends: `begin`, `test` (tenant, run id, module, title, outcome, time), `end`. File: `reports/cases/tenant-runId.cases.jsonl`. A kill loses nothing already written; a truncated last line is dropped by `parseCaseLog`; a missing `end` means `incomplete` while the lines still count. The tenant is taken from the run's own context, never looked up later.

## Latest valid per tenant (combine)
- Newest result wins per (tenant, case); a **skipped** result never overwrites a real one; within one run the worst outcome wins.
- A **partial run cannot replace the latest pointer**: a one-spec debug run must not publish a green board (`canReplacePointer`).
- Aggregate cells are recomputed at combine time from current scope, not stored.
- The merged view is for **status, never a release gate**.
- Store it as workflow artifacts or on a results branch, never on the main branch (`references/ci.md`).

## CI result from the summary
The test step runs with continue-on-error so reports and artifacts always publish. A final `always()` step runs `check-summary.ts` (Model A) or `combine-cli.ts` (Model B) and fails the job if the summary is missing, empty, or any expected tenant failed or ran nothing. A reviewed pipeline also mailed a "NO RESULTS" body when the suite crashed before writing a summary.

## Extras worth keeping
- A reporter that reads the retained trace and names the failing cause (for example a dead micro-frontend chunk) and cannot fail a test: one defect was misdiagnosed as a grid timeout for nine days.
- A run-id prefix for unit runs so sandbox negatives do not pollute drift reports.
- A trend snapshot with a delta gate (fail on a drop over 5 points) for one reference tenant.
