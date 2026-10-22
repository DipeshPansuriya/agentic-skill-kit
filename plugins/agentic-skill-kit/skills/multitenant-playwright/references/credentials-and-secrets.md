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
Artifacts (HTML report, traces, JSON, logs, screenshots with typed text) can contain credential values, for example a password typed into a form or sent in a request header.
- `templates/scrub-artifacts.ts` replaces every credential value in text artifacts in these forms: plain, JSON-escaped, HTML-escaped, URL-encoded.
- Replacement runs longest value first (so `admin` never cuts `admin123!` in half) and also covers base64 forms, including base64 of `user:password` (a Basic auth header). Base64 is matched in its aligned form only (**verify**: an embedded value at another offset is not found).
- A secret shorter than 4 characters cannot be scrubbed without destroying the artifact: the scrub **fails** (use longer test credentials).
- Anything that may contain a value and cannot be rewritten is **deleted**: every `.zip` (traces and report data are compressed) and any binary that contains a value. The step then exits non-zero so a person notices. Decision: CI runs with `trace: 'off'` because traces would be deleted anyway; keep traces locally. To keep them in CI, add a zip rewriter first (not shipped). Images cannot be scanned for typed text, so do not type real secrets into visible fields in traced or screenshot tests.
- If no credential value can be resolved, the scrubber refuses (exit 1): it cannot prove the artifacts are clean.
- Run the scrub as its own step (`id: scrub`, `continue-on-error`, `if: always()`) while the credentials file still exists, and **publish artifacts only when it succeeded**: `if: always() && steps.scrub.outcome == 'success'`. A failed scrub therefore publishes nothing, and the final gate (`check-summary.ts` with `STEP_OUTCOMES`) fails the job. Then remove the credentials file.
- In the write step, also validate the file shape with `jq` (a non-empty object of string values; a byte-order mark makes `jq` fail) and emit `::add-mask::` for every value. GitHub does not mask individual fields of a JSON blob on its own (**verify** in your runner with a test echo); multi-line values need explicit redaction: `::add-mask::` covers SINGLE-LINE values only, so a multi-line
  secret must be split per line (each line masked) or redacted before it reaches any log or artifact.
  GitHub-native multi-line masking behaviour: **verify** in your runner with a test echo - do not rely on it.

## Detecting leaks in the PR pipeline
A contract test fails the PR when the pipeline file assigns a literal to a variable whose name contains PASSWORD, SECRET, TOKEN or KEY (`templates/unit-decide.spec.ts`). Run the repository's secret scanner as well; both are heuristics.

## Scrubber residual limits (templates/scrub-artifacts.ts header)

Covered: plain, JSON-escaped, HTML-escaped, URL-encoded and base64 (aligned) forms, plus ONE level of
URL-encoding or any-alignment base64 found by both the text and the binary scan; file names holding a secret
value are renamed into `[scrubbed]`; symlinked artifact paths are refused. NOT covered: two or more NESTED
encoding levels, partially- or mixed-encoded values, binary content (deleted outright - or kept loudly with
`SCRUB_KEEP_BINARY=1`, which still fails the step), image pixels, and secrets shorter than 4 characters
(the run fails instead of scrubbing). Auth/session state is written mode 0600 and the run fails when the
state dir is not git-ignored (`templates/cache.ts`).
