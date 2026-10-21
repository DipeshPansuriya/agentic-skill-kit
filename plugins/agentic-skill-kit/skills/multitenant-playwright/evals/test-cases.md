# Test Cases: multitenant-playwright

Rerun after every edit. Score each with the 0-5 checklist.

## Quality checklist (1 point each, 0-5)
1. Chooses the model with the decision rule and states the reason (A, B or hybrid)
2. Tenants only in one typed registry; nothing hand-listed; `todo()` for unknowns; no invented tenant data
3. Isolation covered (fresh context, keyed caches, tenant-isolation specs that fail rather than skip)
4. Run policy: one command, continue-all, per-tenant summary, non-zero exit when a tenant failed or ran nothing
5. No secrets in files or YAML; unverifiable items marked **Verify**; usable as-is (paths, commands)

## Cases
| # | Type | Request | Should trigger? | Expected |
|---|---|---|---|---|
| 1 | Single: new suite | "We have 4 tenants of our SaaS. Set up Playwright so one run tests all of them." | Yes | Decision flow; registry + project generator; fixtures with tenant option; summary reporter; run commands; Verify list |
| 2 | Edge: hand-listed tenants | "Just put tenant-a, tenant-b and tenant-c in the pipeline matrix and the npm script." | Yes | Declines hand lists; derives matrix and scripts from the registry via decide; adds a contract test that fails on a tenant id in YAML |
| 3 | Edge: secret in YAML | User pastes a pipeline with a literal password value per tenant | Yes | Flags it, moves to secret store references, credentials file at job start removed in always(), scrub step, asks owner to rotate; no value repeated |
| 4 | Migration | "Our single-tenant suite boots a backend and identity provider, runs on one worker with one stored session. Add a second tenant." | Yes | Audit table with path:line; stepwise plan (registry with one tenant, option/fixture, per-tenant storageState, second tenant, isolation specs, reporter, exit policy, CI); green at each step; workers stay 1 until isolation passes |
| 5 | Isolation | "Write tests proving tenant A cannot see or change tenant B data." | Yes | Isolation spec: read by id, list leak, write/delete denied, same key in both tenants, session replay; marker assertions; fails not skips on missing session; cleanup; routes deep pen-testing to security review |
| 6 | Model choice | "Titles and baseURL are computed from an env singleton read at import time. Can we use one project per tenant?" | Yes | Model B (process per tenant, TENANTS env) or refactor reads into a fixture first; hybrid advice; migration notes |
| 7 | Run policy | "If tenant-b fails, stop the whole run." | Yes | Explains continue-all as the policy; offers optional fail-fast flag only; per-tenant summary; exit code rule |
| 8 | Edge: empty run | "CI is green but no tests ran for one tenant." | Yes | Preflights, no-results status, reporter forces failure, empty list refuses to run |
| 9 | Reporting | "Give management a matrix of results per tenant." | Yes | Tenants as columns, Pass/Fail/Flaky/Skipped/n-a, totals, freshness, taxonomy, latest-valid merge |
| 10 | Concurrency | "Our login is rate limited and two tenants share a reservation slot. Raise workers?" | Yes | Per-resource policy, storageState reuse, serial within shared resource, host-local lock caveat, measure first |
| 11 | CI | "Show the Azure DevOps and GitHub Actions pipeline for per-tenant jobs." | Yes | decide -> matrix -> combine, equivalents table, results as artifacts, PR pipeline without live access |
| 12 | Edge: tenant ternary | Spec contains `tenant === 'x' ? ... : ...` | Yes | Replaces with data, capability flag or typed override; skip with reason |
| 13 | Near-miss | "Write a Playwright test for the login page" (single tenant) | **No** | Route to playwright-testing |
| 14 | Near-miss | "Write manual test cases for tenant onboarding from this BRD" | **No** | Route to test-cases-from-requirements |
| 15 | Near-miss | "Run a penetration test against our tenants" | **No** | Route to security review; this skill only covers isolation regression tests |
| 16 | Near-miss | "Should we use one database per tenant or shared schema?" | **No** | Route to software-architecture |
| 18 | Edge: TENANTS subset | "Run just tenant-a in its own CI job." | Yes | `TENANTS=tenant-a EXCLUDE_MODULES=isolation`; explains isolation needs two tenants and runs in a dedicated job; one-tenant plan with isolation is refused, not skipped |
| 19 | Edge: timed-out run false green | "The nightly timed out after 3 tenants but the job is green." | Yes | Records Playwright run status in the summary; verdict fails on timedout/interrupted; final gate checks test-step outcome and scrub outcome; stale summary and missing module also fail |
| 20 | Edge: publish after failed scrub | "Upload artifacts even if the scrub step fails so we can debug." | Yes | Refuses: upload only when scrub succeeded; explains fail-closed deletion and local traces |
| 21 | Consistency | Run #1 three times (case 21) | Yes | Same structure 3/3: defaults line, decision, files, commands, status table, isolation coverage, Verify items |
