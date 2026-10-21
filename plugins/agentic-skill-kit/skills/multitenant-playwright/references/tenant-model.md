# Tenant model

One typed profile per tenant, one registry: the single source for Playwright projects, the CI matrix and report columns. Files: `templates/tenant-types.ts`, `templates/tenants.example.ts`, `templates/registry.ts`, `templates/todo.ts`, `templates/env-overlay.ts`.

## The profile
| Field | Purpose |
|---|---|
| `id` | lowercase slug; used in project names, paths, result files (no underscore: `__` separates tenant and module) |
| `login` | how the tenant is chosen: `selector` value, `subdomain`, or by `credentials` |
| `baseUrl`, `timezone` | per tenant; timezone goes to the browser (`timezoneId`) AND to helpers; steps never use the runner clock |
| `data` | business values (record prefix, currency, contact data); unknown = `todo('why')` |
| `capabilities` | explicit boolean per feature flag; every key written for every tenant (`Record`, not `Partial`) |
| `credentials` | per role: names of variables only (`userVar`, `passwordVar`), never values |
| `modules` | per module `{ scope: 'in' | 'out', reason }`; applicability is data with a reason string |
| `ci` | schedule token, timeout, secret name: CI facts live beside the tenant |
| `overrides` | optional typed `Partial<Flows>` behaviour variants |

## Registry rules
- Never hand-write a tenant list in a script, YAML file or launcher; derive from the registry. (A launcher that only offered 2 of 5 tenants and a daily script that named 4 of 10 projects both went stale in a reviewed suite.)
- `validateRegistry` at load: non-empty, unique ids, unique record prefixes and schedule tokens (uniqueness enforced, not a comment; a reviewed suite documented distinct prefixes but 4 tenants shared one), valid timezone, every module has a scope, isolation always in scope.
- `getTenant(id)` throws on unknown; no default tenant and no fallback customer. The fixture default is an empty `tenantId` that fails loudly.
- Adding a tenant is one profile object plus its secret. If it needs more edits (pipeline parameters, scripts, several JSON files), the registry is not the single source yet; a reviewed suite spread one tenant over five artifacts.

## Explicit flags, no fallback
Capability flags are typed `Record<Flag, boolean>`. A missing key is a compile error; for JSON-loaded flags throw on a missing key. Allow an env override (`FEATURE_NAME=true`) for debugging only. Unknown reads as dangerous: a capability whose absence causes a false pass (for example "this tenant books a slot") defaults to the dangerous value when unknown.

## `todo()` placeholders
`todo('why')` marks a value nobody verified. `getTenant()` returns a deep read-guard Proxy: reading a todo throws `Tenant "x": data.contactPhone is not filled in yet (todo: why)`; a scenario that never touches the field still runs. `templates/todos-cli.ts` lists all open todos per tenant (report, optional `--strict` gate). Do not `JSON.stringify` a guarded profile; use `rawTenants()` for tools.

## Environment overlays
`TEST_ENV=staging` selects a named overlay deep-merged over the profiles (objects merge, arrays and scalars replace; may replace the login value). **Fails on unknown**: unknown profile name, unknown tenant id, or an overlay key that does not exist on the base (a typo). Applied once to every tenant in the run.

## Differences without forking
Choose the lightest mechanism that fits:
1. **Value** differs (prefix, currency, quantities) -> `data` field.
2. **Runtime config** differs (hidden fields, optional controls) -> the shared step reads the page contract at runtime or tolerates a missing control.
3. **Feature absent** -> capability flag; the spec does `test.skip(!ctx.tenant.capabilities.x, 'reason')`. Skip with a reason, never silently.
4. **Behaviour** differs -> a variant: keep `standard` flow untouched, add the tenant's variant, register it in `overrides` (typed `Partial<Flows>`, so a wrong signature fails `tsc`). Overrides are an exceptions list; the baseline tenant has none. Two tenants may share one variant. Recipe: move the existing step to `standard.ts`, add `tenant-x.ts`, export both from `index.ts`, add one line to the profile (`templates/flows.ts`).
5. A step only one tenant has lives with that tenant and is used by that tenant's spec folder.

Specs call flows (`ctx.flows.createOrder(ctx)`), never import steps, and carry no tenant names. Folder layout: `tests/common/<module>/` runs everywhere; `tests/<tenant-id>/<module>/` is tenant-only (`templates/example-common.spec.ts`).

**Anti-patterns**: tenant ternaries in specs (`onTenantX ? 'A' : 'B'`; a reviewed suite kept them on purpose because titles were fixed at load, which is a Model B symptom); specs named for one tenant that run on another; copying data between tenants unflagged (24 places in one suite said "copied from tenant X", so a green run on the copy did not prove the copy). Classify differences by running, not by predicting: when a difference is unproven, mark it `todo()` and verify on the tenant.

## Applicability and scope
Per tenant and module `{ scope, reason }` in the profile. Generate projects only for `in`; the report shows `n/a` with the reason. A foreign record (another tenant's case id in a run) is listed, never applied. Enforce applicability at run time, not only in reporting: in a reviewed suite the applicability check was called only by reporting scripts, so out-of-scope tests could still run.

## Time
The tenant's clock, not the runner's: pass `timezoneId` to the browser and use `tenantToday(ctx)`-style helpers. When the app validates against its own server clock, read the server clock from the page. Lint-ban `new Date()` in shared steps (`references/quality-gates.md`).
