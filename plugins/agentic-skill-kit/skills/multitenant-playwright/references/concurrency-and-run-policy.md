# Concurrency and run policy

## Workers policy
- Default `workers`: Playwright's default locally; a small fixed number on CI (3 in a reviewed suite) set by `PW_WORKERS`. Raise only after measuring contention on the shared environment.
- Why small: every worker is another session on a shared test environment; one reviewed suite measured a sequence-number stored procedure as its top deadlock source. A measured reason beats a guessed one.
- Headed browsers serialise (windows occlude each other and covered renderers freeze); headed-only is an app-specific constraint, not a default. Note: `isHeaded`-style checks in the config are only valid for the runner process because the config is re-evaluated inside workers.
- `fullyParallel: false` keeps tests in a file ordered; files spread across workers. Set `fullyParallel: true` only when every test is independent.

## Serial vs parallel, per resource
| Resource | Policy | Why |
|---|---|---|
| Login endpoint with a per-IP rate limit (5 per IP per minute in one suite) | Log in once per role per TTL via `storageState`; run setup serially | 27 logins per run became about 3 |
| Shared slot or global counter (booking slots, sequence numbers) | Serial within the tenant, or a lock around the critical section | The app clears a form and the new number is learned as "the row that appeared" |
| Per-environment limits | **Tenants in parallel**, tests within a tenant serial where needed | Limits are per environment, not global |
| Pure read tests | Parallel | No shared state |
Record the real reason in a short ADR and correct it when wrong: one suite's first rationale (session eviction) was disproved and the ADR kept the correction.

**One process cannot cap concurrency per tenant** (shared worker pool). If a tenant needs "serial inside, parallel across", use Model B (`references/fan-out-models.md`), or put that tenant's tests in serial describes (`test.describe.configure({ mode: 'serial' })`).

## Locks
- A file lock (`fs.writeFileSync(path, ..., { flag: 'wx' })` in the temp directory, with stale takeover after minutes) is valid on **one host only**. It also serialises every tenant on that host if the lock is not tenant-scoped. Do not shard across agents on it.
- Prefer designs that need no lock: unique data per test, per-tenant resources, server-side claims. If a lock is unavoidable, key it by tenant + resource and document that it is host-local.
- Claims files ("this number is taken") appended to a temp file have the same host-local limit.

## Unique data with enforced uniqueness
- Generate from the tenant prefix + run id + worker index + a worker-level sequence (`ctx.unique(kind)` in `templates/fixtures.ts`). The set and counter live at module scope, so values stay unique across all tests that one worker runs, and the worker index separates workers; a duplicate throws.
- Tenant prefixes are unique by registry validation, not by a comment. A reviewed suite said prefixes were distinct "on purpose" while four tenants used the same one; with random digits the collision odds were low but not zero.
- Real data is created on the target every run; cleanup in `finally` where the product allows, and staging or UAT only.

## RUN POLICY
1. **ONE command / run completes ALL selected tenants.** Model A: `npx playwright test`. Model B locally: `npx tsx run-all.ts` (`templates/run-all.ts`); in CI the matrix is the same idea.
2. **Continue-all.** A failing tenant never stops the others. Do not set `maxFailures` or `-x` in config. In B, `fail-fast: false`; in `run-all` the loop continues.
3. **Optional `--fail-fast`**, cheap: Model A pass `--max-failures=1` (stops the whole process); `run-all.ts --fail-fast` stops launching further tenants and the exit is still non-zero.
4. **Per-tenant pass/fail summary at the end** (reporter `onEnd` and `run-all`): one line per tenant with status and counts.
5. **Exit code non-zero** if any tenant failed, ran nothing, has no usable credentials, has its environment down, or the list was empty. The reporter can force `failed` even when Playwright says passed (`onEnd` returns `{ status: 'failed' }`). Never use `--pass-with-no-tests`.
6. **Preflights** (`templates/preflight.ts`, `templates/auth.setup.ts`, `templates/global-setup.ts`):
   - empty or unknown tenant selection refuses to run (global setup, `selectTenants`);
   - no usable credential for a tenant (missing or placeholder) fails that tenant's setup project and writes a marker;
   - environment down: probe the base URL with retries on transient errors only, write the marker; a login page that loads while the API tier is down once cost three nights of 15/15 failures at "Authentication failed", so probe what login actually needs;
   - one tenant's preflight failure stops only its own module projects, and that tenant is reported failed: a tenant that has a planned module with no reported case is `incomplete`, never green;
   - a run that ends as `timedout` or `interrupted` is never green: the reporter records Playwright's run status in the summary and `verdict()` fails on anything but passed/failed; CI also checks the test step outcome (`STEP_OUTCOMES`);
   - `run-all.ts` rejects a non-integer `--parallel` (exit 2), deletes each tenant's old summary before spawning, and ignores summaries from another run id.
7. A run that executed zero tests or only skips is `no-results`, not a pass.
8. Do not pass `--reporter` on the CLI: it replaces the configured reporters and removes the summary (`run-all.ts` refuses it).

## Quarantine
A known application defect may be tagged (for example `@app-broken` in the title) so its failure is reported as `app-broken`, not red: require a diagnosed cause, a raised defect, and removal as soon as the test passes. Flaky is separate: shown in its own column, never retried to green.
