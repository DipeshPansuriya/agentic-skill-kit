# Isolation

Two meanings, both mandatory: (1) tests do not leak state into each other or across tenants inside the suite; (2) the product keeps tenants apart, proven by tests. The second is the core SaaS risk, so it gets its own section.

## Part 1: isolation inside the suite
- **Fresh context per test.** Playwright's default (new browser context per test). Do not share a page or context across tests. Reuse sessions only through `storageState`, loaded into a fresh context.
- **Per-test run state.** `ctx.run` is a new object per test, created in the fixture, never module-level (`templates/fixtures.ts`). Read it with `requireRun(ctx, key, producedBy)` so a missing value fails naming the step that should have produced it (`templates/flows.ts`).
- **No seed data, no tenant-keyed seed.** Each scenario creates its own records through the UI or API and gives them unique names. Writing test data straight into the database is refused unless an explicit flag allows it.
- **Every cache keyed by tenant** (`templates/cache.ts`):
  - auth state `.e2e-state/auth/<tenant>/<role>.json` with a TTL (30 min in the reviewed suite);
  - prerequisite cache keyed by tenant with a TTL shorter than the data rollover (20 h so a cached job cannot outlive the business-day or reservation-window boundary); only read-only artifacts are cached; the file stores its tenant id and `readPrereq` throws on mismatch (a reviewed note: "a run handed another tenant's record fails at a list filter");
  - bundle or asset caches keyed by host + path, content-hashed files only.
  Keying auth by tenant id, not by host, matters when several environments share one host and the tenant comes from the credentials.
- **Result files namespaced** `tenant-runId` (`resultFile()`), so parallel jobs and reruns never overwrite each other.
- **Leakage guards.** A run recorded for another tenant must not apply (`assertRecordMatchesTenant`, taxonomy `mismatched` in `templates/combine-results.ts`). A foreign record id in a run is listed, never applied.
- **Roles never share cookies**: one context per role (`templates/auth.setup.ts`).
- Tenant-specific data generated with an enforced unique prefix (`references/concurrency-and-run-policy.md`).

## Part 2: tenant-isolation tests (first-class; general SaaS practice, adapt to the product's threat model; hand deep pen-testing to a security review)
The skeleton is `templates/tenant-isolation.spec.ts`. It lives in `tests/common/isolation/`, runs once per tenant (that tenant is the attacker) against every other tenant (the victim), and needs both tenants' sessions in the same process (Model A) or a dedicated isolation job (Model B).

Required patterns, UI and API:
1. **Read by id**: tenant B requests tenant A's record id. Expect 403 or 404, never 200, and the body must not contain A's marker value.
2. **List and search**: B's list, search, autocomplete, counts and exports do not contain A's marker.
3. **Write**: B's update and delete of A's record are denied, then A's record is read back unchanged.
4. **Same id or natural key, different tenant**: create the same reference in both tenants; each sees only its own value, no merge, no uniqueness error that reveals the other tenant's data.
5. **Session replay**: A's session cookies or token sent to B's host are rejected (401/403/redirect to login).
6. **Tenant selector tampering**: change the tenant in the header, query string, path, body field or login dropdown while holding A's session; expect denial. Include mass assignment: create a record with a body field naming another tenant and expect it ignored or rejected.
7. **Error oracles**: 403 vs 404 differences, error text and timing must not reveal that another tenant's record exists (decide the policy and assert it).
8. **Indirect channels**: file downloads and signed URLs, notifications and websockets, background-generated reports and emails, caches and search indexes. Add one test per channel the product has.
9. **Role boundary inside a tenant** (a read-only role cannot write) as the neighbouring check.

Rules:
- Production guard (staging-only): the isolation spec refuses to run unless every involved base host is
  on `TENANT_ISOLATION_ALLOWED_HOSTS` (comma list of `host[:port]`); without the variable, or with a host
  missing from it, it SKIPS with that reason. Destructive isolation checks therefore never touch production
  by default - the allowlist env is the gate, not prose (`templates/isolation-helpers.ts:isolationHostGuard`).
- Destructive calls (update, delete with the victim's id) run only after the read check proved the id does not resolve in the attacker tenant; with sequential ids the same number may be the attacker's own record, so prefer GUID ids and keep a canary record that must survive. Non-production data only. Prefer dedicated users and run isolation in its own job so its cleanup cannot disturb other specs.
- A replay test builds Cookie/Authorization headers explicitly from the stored state (`templates/isolation-helpers.ts`): storage-state cookies are domain-scoped and an API context never sends local-storage tokens, so loading the state against another host sends nothing and passes vacuously. Always add a control request that must succeed on the home host.
- Wait for a positive denied state in the UI (a not-found or access-denied message) before asserting a marker is absent.
- Isolation tests must **fail, not skip**, when a session is missing; a skipped isolation test is a false green. The only legitimate skip is the self pair (`attacker === victim`) with a reason.
- Create the victim record with a unique marker (`ctx.unique('isolation')`) and delete it in `finally`, on staging data only.
- Assert on the marker in response bodies and the DOM, not only on status codes.
- Every tenant is in scope for isolation; `validateRegistry` rejects a profile that excludes it.
- Findings that show real cross-tenant access are security findings: stop, preserve the repro, and route to security review rather than retrying or hiding.

## Marking what is verified
The two reviewed suites enforced Part 1 (keyed caches, namespaced results, mismatch guard). Part 2 patterns are standard multi-tenant test practice, not taken from the reviews: treat endpoint paths, status codes and UI text in the template as **Verify**.
