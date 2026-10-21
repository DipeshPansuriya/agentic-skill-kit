# Fan-out models: one process or one job per tenant

Both models were found in real suites. Pick with the rule below; the same `playwright.config.ts` serves both (`templates/playwright.config.ts`).

## Model A: one process, one project per tenant x module
- Projects are generated from the registry: `registry.flatMap(tenant => modules.map(module => project))`. Each project sets `use.tenantId` (an `option: true` fixture, `templates/fixtures.ts`), `baseURL`, `timezoneId`, `storageState`.
- `common/<module>/` specs run on every tenant; `<tenant>/<module>/` specs are tenant-only. Titles are identical across projects, so reports line up by row.
- One command (`npx playwright test`) runs everything; one worker pool is shared, so tenants interleave.
- Proven in a suite with 5 tenants x 2 modules = 10 projects. The tenant was picked from a login dropdown; no tenant-specific value was read at module load.

**Valid only when** the tenant is chosen at login or by an option AND nothing reads the tenant at module load: no cached environment object, no title built from the tenant, no baked `baseURL`/timezone/reporter option, no top-level read of tenant-specific env.

**Costs**: one machine or agent (no horizontal scale; `--shard` splits tests but each shard still runs every tenant it holds), shared workers (no per-tenant concurrency limit is expressible in one process; **verify** for your Playwright version), and one tenant's global problem can affect all (keep preflights per tenant inside its setup project, not in global setup).

## Model B: decide -> one job per tenant -> combine
- A pure `decide()` picks the tenants (schedule token, manual flags) and fails instead of skipping when nothing is selected. One job per tenant runs a separate process with `TENANTS=<id>`. A `combine` job collects results and derives the pipeline verdict.
- Proven in a suite with 4 tenants: the single-process design was considered and rejected because the tenant was read from `getEnvironment()` at ~55 module-load sites, and titles were built from the tenant (so ids bound results to the right registry entry).
- Per-tenant jobs run in parallel on separate agents; inside a job the run stays serial where the app needs it (login rate limit, shared slot). Limits are per environment, so tenants parallelise safely.

**Needed when** config, titles or URLs are fixed at module load; the same spec needs different titles per tenant or per actor; there are per-tenant limits, schedules, run windows or secrets; or wall time needs horizontal scale (one tenant took about 3 h serially).

**Costs**: pipeline plumbing (decide, matrix, combine), one runner per tenant, and isolation specs need a job that holds the pair's sessions. Gotcha seen in practice: a design claimed "adding a tenant is one template call" but needed edits in 5 pipeline places. Derive the matrix from the registry and add a contract test (`templates/unit-decide.spec.ts`) so YAML and registry cannot drift.

## Decision rule
| Question | A | B |
|---|---|---|
| Tenant chosen at login/option only? | yes | either |
| Anything read at module load that depends on the tenant? | no | yes |
| Titles must differ per tenant/actor? | no | yes |
| Need per-tenant rate/slot limits or run windows? | no | yes |
| Need more than one agent for wall time? | no | yes |
| Per-tenant secrets/blast radius required? | one credentials file | one per job |
| Simplicity and one report wanted? | yes | needs combine |

Any "B" answer in rows 2 to 5 means B. Otherwise start with A; it is cheaper.

## Hybrid (recommended default for a growing suite)
- One config; `TENANTS` (comma list, empty = all) decides which projects exist.
- Local runs and smoke: A. Scheduled pipeline: B with the matrix derived from the registry; a job may hold several tenants (`TENANTS=a,b`) to cap runner count.
- Isolation specs: one dedicated job (or an A-style run) that selects every tenant in the pair, because it needs both sessions.
- Same summary format from both (`templates/summary.ts`), so `check-summary` and `combine-cli` read either.

## Migrating A to B
1. Confirm per-process outputs: `REPORT_DIR` and `STATE_DIR` come from env (already in `templates/cache.ts`), results are named tenant + run id.
2. Prove a single-tenant run: `TENANTS=<id> npx playwright test` is green and its summary lists only that tenant.
3. Split credentials per tenant (one secret per tenant, referenced by `ci.credentialsSecret` in the profile).
4. Add `decide` + matrix (`templates/pipeline-model-b.yml`, `templates/decide-cli.ts`) and `combine` (`templates/combine-cli.ts`). Keep the A pipeline until B is green twice.
5. Move isolation specs to their own job with the pair's credentials.
6. Add the pipeline contract test; retire the A pipeline.
No spec changes are needed; if one is, a spec read tenant state at module load: move that read into the fixture first.

## Verify list (not proven by the reviews)
- `--project` accepts glob patterns like `tenant-a__*` in your Playwright version.
- `RUN_ID` set in `globalSetup` reaches workers (the templates fall back to a per-process id).
- `config.projects` in a reporter lists only the projects selected on the command line.
- `secrets[matrix.name]` dynamic lookup in your CI product.
