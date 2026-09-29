# CI/CD Quality Gate

This gate runs 4 of the kit's scanners on every pull request. It fails the build on HIGH or CRITICAL findings.

| Scanner | Checks | Files |
|---|---|---|
| security | Secrets, SQL injection, unsafe deserialization, TLS/CORS misconfiguration, debug settings (CWE-tagged) | code, config, .env, IaC |
| performance | Sync-over-async, I/O and DB calls inside loops, linear lookups in loops, SELECT * | .cs .java .py .ts .js |
| sql | UPDATE/DELETE without WHERE, non-SARGable predicates, NOT IN traps, dynamic SQL | .sql |
| playwright | test.only, hard waits, missing await, hard-coded credentials, brittle selectors | *.spec.* / tests / e2e |

## Setup (5 minutes)
1. Copy `plugins/agentic-skill-kit/skills/` and `ci/` from this repo into your project as `.skill-kit/skills/` and `.skill-kit/ci/`.
2. **GitHub:** save `github-actions-kit-scan.yml` as `.github/workflows/kit-scan.yml`.
   **Azure DevOps:** create a pipeline from `azure-pipelines-kit-scan.yml`, then add it as a Build Validation policy on your target branch.
3. On an existing codebase, accept today's findings once so only new problems fail builds:
   ```bash
   python .skill-kit/ci/kit_scan.py --kit .skill-kit --write-baseline .skill-kit/baseline.json .
   ```
   Commit `baseline.json`. The pipelines pick it up automatically.

## Local use
```bash
python .skill-kit/ci/kit_scan.py --kit .skill-kit .                    # whole repo
python .skill-kit/ci/kit_scan.py --kit .skill-kit --changed origin/main # only files changed vs main
python .skill-kit/ci/kit_scan.py --kit .skill-kit --only security,sql --fail-on MED src/
```

## Behaviour
- In a PR, only changed files are scanned. On main, the whole repo is scanned.
- The results summary appears in the GitHub job summary or the Azure DevOps Summary tab.
- SARIF output goes to GitHub code scanning, or to the Azure DevOps Scans tab with the SARIF extension.
- Findings in test files and generated files (`*.gen.ts`, `*.g.cs`, `*.designer.cs`) are downgraded to LOW or skipped.
- To silence a reviewed security line, add `nosec`. To accept existing findings in bulk, use the baseline.

## Tested
- In a git repo, PR mode caught all 9 planted problems in 3 changed files and exited with code 1.
- With a baseline, the same PR exited with code 0.
- The SARIF output is valid JSON with one run per scanner.
- The workflow passes `actionlint`.
- A full scan of spring-petclinic reported 1 HIGH, a real hard-coded Kubernetes password.

These are heuristic leads, not proof of a problem. The gate complements CodeQL, SonarQube and Dependabot/`npm audit`; it doesn't replace them.
