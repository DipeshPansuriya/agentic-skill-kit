# Credentials and secrets

## Model
- The registry holds **references** (variable names) per tenant and role: `credentials: { operator: { userVar, passwordVar } }`. Roles are the abstraction (an `admin`, an `operator`, a dual-rights identity); credentials are per tenant AND per role.
- Values come only from the secret store: environment variables mapped from a CI secret or variable group, or a credentials file the pipeline writes at job start. `templates/preflight.ts` reads env first, then `CREDENTIALS_FILE`.
- One shared login for all tenants (the tenant chosen in a dropdown after login) is allowed by some products, but then concurrency of the same user across tenants and workers is **unverified**; test it before raising workers.

## Rules
1. **Never in YAML, code, JSON committed to the repo, memory files or logs.** A reviewed pipeline held a literal function key and subscription and tenant identifiers in plain text, and its lint explicitly allow-listed them; that is the example not to copy. Report such a finding to the owner for rotation; do not hide or reuse it.
2. **Template with placeholders counts as unusable.** `CHANGE_ME`, `TODO`, empty, `****` and `<...>` are rejected by `readCredential`. About 60 tests once skipped when credentials were missing; a missing secret must never report green.
3. **Credentials file lifecycle**: written at job start (`umask 077`, BOM-less, shape-validated), path exported as `CREDENTIALS_FILE`, removed in an `always()` step even when tests fail (`templates/pipeline-model-b.yml`). Git-ignore `*.credentials.json` and `.env`; keep only a placeholder template in the repo.
4. **One secret per tenant** in Model B (named by `ci.credentialsSecret`), so a job sees only its own tenant's values. In Model A one secret holds a map of all variable names to values.
5. **Local runs**: a launcher may remember non-secret settings (URL, environment name, browser) in a git-ignored file and must ask for the password each time, never saving it.
6. **No auth bypass**: the suite logs in like a user. Do not add test-only backdoors to production code to avoid login.

## Artifact scrubbing (fail closed)
Artifacts (HTML report, traces, JSON, logs, screenshots with typed text) can contain credential values; a live password was once published this way.
- `templates/scrub-artifacts.ts` replaces every credential value in text artifacts in these forms: plain, JSON-escaped, HTML-escaped, URL-encoded.
- Anything that may contain a value and cannot be rewritten is **deleted** (archives and binaries), and the step exits non-zero so a person notices. To keep trace archives, unpack, rewrite and repack with a zip library (verify before relying on it).
- If no credential value can be resolved, the scrubber refuses (exit 1): it cannot prove the artifacts are clean.
- Run the scrub before the upload step, in an `always()` step, while the credentials file still exists; then remove the file.
- Prefer `trace: 'retain-on-failure'`, and avoid typing real secrets into fields in traced tests where the product offers a token login.

## Detecting leaks in the PR pipeline
A contract test fails the PR when the pipeline file assigns a literal to a variable whose name contains PASSWORD, SECRET, TOKEN or KEY (`templates/unit-decide.spec.ts`). Run the repository's secret scanner as well; both are heuristics.
