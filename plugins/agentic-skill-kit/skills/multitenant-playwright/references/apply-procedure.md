# Apply procedure

Two paths: enhance an existing single-tenant suite, or scaffold a new one. Rule for both: **tests stay green at every step**; commit after each step; compare pass counts and `npx playwright test --list` before and after.

## A. Existing Playwright project: audit (what is single-tenant today)
Search and note each hit with `path:line`:
- Tenant fixed in config: one `baseURL`, one timezone, one locale, constants read at module top level, a cached environment object.
- One identity: a single stored session file (`storageState`), one user/password pair, one auth setup.
- Titles or ids built from environment values at load.
- Serial run on one worker (`workers: 1`, `fullyParallel: false`) and why (rate limit? shared data? the real reason, measured).
- Global setup that boots a real backend and an identity provider, seeds data, or logs in once.
- Fixed record ids, seed data, or data assumed to exist; any shared test data not keyed by tenant.
- Result, cache and report files without a tenant in the name; a reporter that does not know tenants.
- A CI file that runs one job, hard-codes one environment, or ignores the exit code.
- Secrets in files or YAML.
- Output: a short audit table (finding, path:line, risk, step that fixes it).

## Safe stepwise migration
0. **Baseline**: run the suite, record test count, pass count and duration. Create a branch; no work on the main branch.
1. **Registry with ONE tenant** that mirrors today's implicit tenant (`templates/tenant-types.ts`, `templates/registry.ts`, `templates/todo.ts`). No behaviour change. Add `unit` tests (`templates/unit-registry.spec.ts`). Gate: same pass count.
2. **Project option and fixture**: add `tenantId` option, the `tenant` and `ctx` fixtures (`templates/fixtures.ts`), and generate the single project from the registry (`templates/playwright.config.ts`, `templates/project-name.ts`). Keep the old project name alias until CI filters are updated. Existing specs keep working untouched.
3. **Move constants into the profile** (URL, timezone, data, credential references); read them via the fixture; ban new top-level reads (lint). Gate: same pass count.
4. **Per-tenant storageState**: setup project per tenant, state path keyed by tenant and role with a TTL (`templates/auth.setup.ts`, `templates/cache.ts`). One tenant still uses one file, at the new path. Update ignore rules.
5. **Key caches and result files by tenant and run id**; add the leakage guards.
6. **Second tenant**: add the profile with `todo()` for unknowns, explicit capability flags and scope reasons; run its smoke first; split `common/` and tenant-only folders; skip with reasons.
7. **Isolation specs** (`templates/tenant-isolation.spec.ts`, `references/isolation.md`): API level first, then UI. They need both tenants' sessions.
8. **Matrix reporter and exit policy** (`templates/summary-reporter.ts`, `templates/check-summary.ts`, `templates/preflight.ts`, `templates/global-setup.ts`): one command, continue-all, non-zero when a tenant fails or runs nothing.
9. **CI**: Model A first (`templates/pipeline-model-a.yml`); move to B only if the decision flow says so (`references/fan-out-models.md`); add the PR pipeline and contract tests (`templates/pipeline-pr.yml`, `templates/unit-decide.spec.ts`).
10. **Gates**: architecture lint and ratchet baselines (`references/quality-gates.md`); scrub step and credentials-file lifecycle (`references/credentials-and-secrets.md`).

### Special case: the suite boots its own backend and identity provider, runs serially, one stored session
- Treat tenants as data inside the booted backend: seed tenant records and users in the harness (not shared mutable data), and give the identity provider one realm or client per tenant, or one user per tenant and role. Details depend on the product: **verify** with the harness owner.
- Start the backend once (`webServer` or global setup), not once per tenant. Model A fits; keep `workers: 1` until isolation specs pass for two tenants, then raise workers one step at a time and re-measure.
- One stored session becomes `auth/tenant/role.json` files; the setup project per tenant logs in through the identity provider once per TTL.
- Isolation specs are cheapest here: both tenants live in the same booted backend, so run them first.
- The preflight is the harness health check (backend and identity provider reachable) and still writes a marker per tenant.

## B. New project scaffold
1. Write the architecture note (parallelism, stages, environments, tenants, run policy) and get it reviewed before specs.
2. Copy the templates into the test directory, keeping the relative imports (`auth.setup.ts` and specs go under `tests/`; fix their import paths).
3. Fill `tenants.example.ts` with 2 tenants (rename the file), with `todo()` for unknowns; set `MODULES`.
4. Run `UNIT=1 npx playwright test --project=unit`, then `npx playwright test --list`.
5. Write the first common spec through `ctx.flows`, then the isolation spec, then the second tenant's folder only if behaviour differs.
6. Add the reporter and exit policy, the PR pipeline, then the scheduled pipeline for the chosen model.
7. Add `.gitignore` entries: `.e2e-state/`, `reports/`, `*.credentials.json`, `.env`.
8. Record a manual test baseline in the same change as the automation (manual steps and automation updated together).
