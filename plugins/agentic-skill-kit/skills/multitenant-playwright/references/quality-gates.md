# Quality gates

Files: `templates/lint-architecture.ts`, `templates/todos-cli.ts`, `templates/unit-registry.spec.ts`, `templates/unit-decide.spec.ts`, `templates/unit-summary.spec.ts`, `templates/pipeline-pr.yml`.

## Lint as architecture
A small script over the shared steps folder, run in the PR pipeline:
- **Hard rules** (any hit fails): shared steps never import tenant data or profiles (tenant knowledge arrives through `ctx` only); no runner clock (`new Date`, `Date.now`; use the tenant clock helper); no quoted business literal typed into fields.
- A reviewed suite also banned `isVisible({ timeout })` (Playwright ignores the option) and literal secret-named values in root YAML.
- Exempt a reviewed line with a trailing `// allow: reason`, and keep a per-file allow list short and documented.
- Add the Playwright ESLint rules `missing-playwright-await` and `no-focused-test` as errors.

## Ratchet baselines (only fall)
Count debt such as `waitForTimeout` calls, `force: true` clicks, raw locators, untagged tests. Commit the counts in a baseline file; the lint fails when a count rises and tells you to lower the baseline when it falls. A reviewed suite held hundreds of fixed sleeps and dozens of forced clicks with ratchets rather than eliminating them; the ratchet stops growth, it does not fix the debt.

## Contract tests so CI and registry cannot drift
- `decide()` against the real registry: whole-word token match, unknown id, empty selection throws.
- The pipeline file contains no tenant id and no literal secret assignment.
- Every schedule name selects at least one tenant; the run list or matrix equals the registry.
- Registry validation: unique ids, prefixes, tokens; valid timezones; isolation always in scope.
- Documentation or rules that are duplicated (for example agent rules and an editor rules copy) are generated from one source with a `--check` drift gate.

## Unit tests of pure logic through the Playwright runner
Registry, overlay, todo guard, decide, verdict, combine and case-log parsing are pure functions; test them with `@playwright/test` in a `unit` project (`UNIT=1 npx playwright test --project=unit`), no browser. A reviewed suite ran about 40 such files.

## Duplicated logic
Never keep two copies of one regex or rule synchronised by a comment. Two success-message regexes in one suite had already drifted apart. Export one constant and import it, or generate the copy and gate on drift.

## Conformance extras
- Tag every test that maps to a requirement; fail on orphan tags and dangling bindings.
- Every write step asserts an outcome (not just "no error") and names the refusal paths of the operation it drives.
- Assertions carry failure messages.
- After three failed attempts to automate a step, record the flow with codegen instead of guessing selectors.
- A selector resolver that tries candidates in order (test id, name, id, label) and logs the winner lets you see selector drift; optional.
