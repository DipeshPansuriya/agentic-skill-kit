---
name: multitenant-playwright
description: "Build or retrofit a multi-tenant Playwright suite: tenant registry, per-tenant projects or jobs, isolation specs, matrix reports. Use when the user asks to test many tenants in one run. Not for single-tenant specs or pentests."
---

# Multi-tenant Playwright

Run one suite against many tenants of a SaaS product: one command, every tenant, one verdict per tenant, and tenant isolation proven. Patterns come from two reviewed real suites (single-process projects, and decide -> job per tenant -> combine) plus Playwright documentation; anything not backed by either is marked **verify**.

## Inputs
- The app: how a tenant is chosen (login dropdown, subdomain, credentials, header), what differs per tenant, and where the suite runs (local, CI agent, self-booted backend).
- Existing Playwright project if any (config, fixtures, auth, CI file) and the tenant list with what is known about each.
- Missing facts become `todo('why')` values or `Needs input`; never invent tenant data.

## Decision flow (read `references/fan-out-models.md` for the proof)
1. Is the tenant picked at login or by an option, and does nothing read it at module load (config, titles, URLs, timezone, cached environment)? **Yes -> Model A**: one Playwright process, one project per tenant x module, tenant as a project option read by a fixture.
2. Titles, config or URLs are fixed at module load, you need per-tenant limits (login rate, shared slots), horizontal scale, or per-tenant secrets and schedules? **-> Model B**: decide -> one job per tenant (`TENANTS=tenant-id` per process) -> combine.
3. Unsure or growing? **Hybrid**: one `playwright.config.ts` serves both (`TENANTS` filters projects). Use A locally and for smoke; B in the scheduled pipeline; isolation specs in one job that holds the pair's sessions.
4. Existing single-tenant suite? Follow `references/apply-procedure.md` (tests stay green at every step). New project? Same file, "New project scaffold".

## Steps
1. State the defaults in one line: model (A/B/hybrid), Playwright version (templates checked on 1.56, strict `tsc`), env names, secret store.
2. Model the tenant as one typed profile in one registry (`references/tenant-model.md`, `templates/tenant-types.ts`, `templates/registry.ts`, `templates/todo.ts`, `templates/tenants.example.ts`, `templates/env-overlay.ts`). Projects, CI matrix and report columns all derive from it.
3. Express differences as data first: value, runtime config, capability flag, then a typed behaviour variant (`templates/flows.ts`, `templates/fixtures.ts`). Specs call `ctx.flows.*`, never import steps, never branch on a tenant id.
4. Generate projects (`templates/playwright.config.ts`, `templates/project-plan.ts`, `templates/project-name.ts`; subset with `TENANTS`, `MODULES`, `EXCLUDE_MODULES`), authenticate once per tenant and role (`templates/auth.setup.ts`, `templates/global-setup.ts`, `templates/cache.ts`).
5. Isolation first-class: fresh context per test, per-test run state, every cache keyed by tenant, and tenant-isolation specs (`references/isolation.md`, `templates/tenant-isolation.spec.ts`, `templates/isolation-helpers.ts`, `templates/example-common.spec.ts`).
6. Concurrency and run policy (`references/concurrency-and-run-policy.md`): ONE command completes ALL tenants, a failing tenant never stops the others, per-tenant summary at the end, non-zero exit if any tenant failed or ran nothing (`templates/run-all.ts`, `templates/check-summary.ts`, `templates/preflight.ts`).
7. Credentials: references only in the registry, values only from the secret store (`references/credentials-and-secrets.md`, `templates/scrub-artifacts.ts`, `templates/scrub-values.ts`).
8. Reporting: tenants as columns, failure taxonomy, kill-resilient case log (`references/result-matrix.md`, `templates/summary.ts`, `templates/summary-reporter.ts`, `templates/case-log.ts`, `templates/combine-results.ts`, `templates/combine-cli.ts`).
9. CI (`references/ci.md`): `templates/pipeline-model-a.yml`, `templates/pipeline-model-b.yml`, `templates/pipeline-pr.yml`, `templates/decide.ts`, `templates/decide-cli.ts`, `templates/schedules.example.json`.
10. Gates (`references/quality-gates.md`): `templates/lint-architecture.ts`, `templates/todos-cli.ts`, unit and contract tests `templates/unit-registry.spec.ts`, `templates/unit-decide.spec.ts`, `templates/unit-summary.spec.ts`, `templates/unit-plan.spec.ts`, `templates/unit-scrub.spec.ts`.
11. Check the result against `references/anti-patterns.md`, run the self-check, and run the suite (`UNIT=1 npx playwright test --project=unit`, then a real run). A test not run is a hypothesis.

## Rules
- A tenant is data. No tenant id, URL, prefix or credential literal outside the registry; no hand-written tenant list in scripts, YAML or launchers.
- Unknown reads as dangerous: unknown tenant, flag, profile or environment throws; no default tenant, no fallback flag value; `todo()` fails loudly on read.
- Tenant isolation specs are mandatory and may never be silently skipped; a missing session fails.
- One run, all tenants. `continue-all`; per-tenant verdict; a tenant that ran nothing, has no usable credentials or has its environment down is a failure, never green. An empty tenant list refuses to run.
- Secrets only from the secret store or variable group; never in YAML, files, logs or artifacts. A credential template with placeholders is unusable.
- Every cache, state file and result file is keyed by tenant (and run id). A record for another tenant is never applied.
- Staging or UAT only; PR pipelines never touch a live environment; results are published as artifacts, never committed to the main branch.
- Flaky tests are reported (flaky column), not retried to green. No `waitForTimeout`, no `test.only`, no `force: true`.
- Mark unverifiable selectors, endpoints and UI text **Verify**; never invent app details.

## Routing
| Need | Read |
|---|---|
| A or B, hybrid, migrating A to B | `references/fan-out-models.md` |
| Profile, registry, flags, overlays, variants, applicability | `references/tenant-model.md` |
| Isolation design and tenant-isolation test patterns | `references/isolation.md` |
| Workers, serial vs parallel, locks, unique data, run policy, preflights | `references/concurrency-and-run-policy.md` |
| Secrets, credential files, scrubbing | `references/credentials-and-secrets.md` |
| Matrix report, taxonomy, case log, latest-valid merge | `references/result-matrix.md` |
| Pipelines for both models, decide script, PR pipeline | `references/ci.md` |
| Lint, ratchets, contract tests | `references/quality-gates.md` |
| What not to copy | `references/anti-patterns.md` |
| Audit, stepwise migration, new-project scaffold | `references/apply-procedure.md` |

## Self-check
- [ ] Model chosen by the decision flow, with the reason stated
- [ ] One registry; `git grep` finds no tenant id, URL or credential literal outside it; no hand-written tenant list
- [ ] Specs contain no tenant ternary and import no steps; differences are data, flags or typed overrides
- [ ] Isolation specs exist, cover read, list, write, same-id and session replay, and fail (not skip) when a session is missing
- [ ] Caches, auth state and result files are keyed by tenant; leakage guards throw
- [ ] One command runs every tenant; exit code non-zero when any tenant failed, ran nothing, or the list is empty
- [ ] No secrets in YAML or files; credentials file removed in an always() step; artifacts scrubbed
- [ ] Reporter derives tenant from the project name, never throws, no-op on `--list`
- [ ] Templates compile under strict `tsc`; unit and contract tests pass; claims without a source are marked verify

## Output
Return: defaults line -> decision (model + reason) -> files (path + code) -> run commands (single tenant, subset, all, unit) -> per-tenant status table -> isolation coverage -> **Verify** items -> `Needs input` list. Test cases: `evals/test-cases.md`.
