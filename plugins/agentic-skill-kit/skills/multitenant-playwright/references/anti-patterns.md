# Anti-patterns: do not copy

Each item was seen in a reviewed real suite.

| Anti-pattern | Do this instead |
|---|---|
| Hand-written tenant lists in scripts, launchers, daily-run commands | Derive every list from the registry; add a contract test |
| Literal secrets in pipeline YAML, plus a lint allow list that blesses them | Secret store only; contract test fails on literal assignments; report the leak for rotation |
| Host-local lock files used for concurrency that may shard across agents | Unique data, per-tenant resources, server-side claims; document a lock as single-host |
| One append-only mega state file as "source of truth" (thousands of lines) | Short current-state file plus dated archives |
| CI committing results to the main branch | Artifacts or a results branch/storage |
| Comments as synchronisation for duplicated regexes or rules | One exported constant, or generated copy with a drift check |
| Tenant-named specs that run on another tenant | Common folder plus tenant-only folders; skip with a reason from data |
| Headed-only as the default | Headless default; headed only when the app demands it, and say why |
| Tenant ternaries in specs and tenant-name checks in shared steps | Data, capability flags, typed overrides |
| Copying data between tenants without a flag | Mark copied values and verify on the tenant, or use `todo()` |
| Prefix uniqueness documented in comments | Enforce in `validateRegistry` and in the generator |
| Applicability computed only in reports | Enforce at run time (project generation, skip with reason) |
| Docs that drift from code (parked features that shipped, folders that do not exist) | Currency markers per doc, ADRs with recorded corrections, a short README that is checked |
| Adding a tenant needs edits in 5 places | One profile plus one secret; derive the rest |
| Vendor-id-in-title schemes and bridge files from a retired test tool | Keep only if you still have a vendor case export |
| Running the suite with `--reporter` override or `--pass-with-no-tests` | Reporters in config; empty runs fail |
| Retrying a flaky test until it is green | Report flaky separately and fix the cause |
| A shared "latest" file overwritten by any run | Latest-valid merge; partial runs cannot replace the pointer |
| Failing the login page probe only (page loads, API tier down) | Probe what login needs; write an env-down marker |
| Unverified assumptions about concurrency (same user across workers) | Measure before raising workers |
| Tenant-less cache or result files | Key by tenant (and run id); verify on read |
