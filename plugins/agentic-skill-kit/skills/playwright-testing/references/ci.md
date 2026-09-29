# Playwright in CI

## Principles
- Pin the Playwright version (`package-lock.json`) and install browsers matching it: `npx playwright install --with-deps` (or only `chromium` for PR runs).
- Or run inside the official image `mcr.microsoft.com/playwright:v<same-version>-noble` (browsers + OS deps preinstalled; required for stable screenshot baselines).
- Secrets (`E2E_USER`, `E2E_PASSWORD`, `BASE_URL`) come from the CI secret store, never the repo.
- Always upload the HTML report and traces, even on failure (`if: ${{ !cancelled() }}` / `condition: succeededOrFailed()`).
- `forbidOnly: !!process.env.CI` fails the run if `test.only` was committed.
- Reporters for CI: `[['html', { open: 'never' }], ['junit', { outputFile: 'results/junit.xml' }]]`, plus `['github']` on GitHub for inline annotations; `blob` when sharding.

## GitHub Actions
```yaml
name: e2e
on:
  pull_request:
  push:
    branches: [main]
jobs:
  e2e:
    timeout-minutes: 30
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        shardIndex: [1, 2, 3, 4]
        shardTotal: [4]
    env:
      BASE_URL: ${{ vars.E2E_BASE_URL }}
      E2E_USER: ${{ secrets.E2E_USER }}
      E2E_PASSWORD: ${{ secrets.E2E_PASSWORD }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: lts/*
          cache: npm
      - run: npm ci
      - run: npx playwright install --with-deps
      - run: npx playwright test --shard=${{ matrix.shardIndex }}/${{ matrix.shardTotal }} --reporter=blob
      - uses: actions/upload-artifact@v4
        if: ${{ !cancelled() }}
        with:
          name: blob-report-${{ matrix.shardIndex }}
          path: blob-report
          retention-days: 7

  merge-reports:
    if: ${{ !cancelled() }}
    needs: [e2e]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: lts/*
          cache: npm
      - run: npm ci
      - uses: actions/download-artifact@v4
        with:
          path: all-blob-reports
          pattern: blob-report-*
          merge-multiple: true
      - run: npx playwright merge-reports --reporter html ./all-blob-reports
      - uses: actions/upload-artifact@v4
        with:
          name: playwright-report
          path: playwright-report
          retention-days: 14
```
- Without sharding: drop the matrix, run `npx playwright test`, upload `playwright-report/` and `test-results/` (traces, screenshots, videos).
- Cache `~/.cache/ms-playwright` keyed on the Playwright version only if install time matters; the official docs recommend not caching browsers (restore time ≈ download time).

## Azure DevOps
```yaml
trigger:
  branches:
    include: [main]
pr:
  branches:
    include: [main]

pool:
  vmImage: ubuntu-latest

variables:
  CI: 'true'

jobs:
  - job: e2e
    timeoutInMinutes: 30
    strategy:
      parallel: 4            # sets System.JobPositionInPhase / System.TotalJobsInPhase
    steps:
      - task: NodeTool@0
        inputs:
          versionSpec: '20.x'
      - script: npm ci
        displayName: Install dependencies
      - script: npx playwright install --with-deps
        displayName: Install browsers
      - script: npx playwright test --shard=$(System.JobPositionInPhase)/$(System.TotalJobsInPhase)
        displayName: Run Playwright
        env:
          BASE_URL: $(E2E_BASE_URL)
          E2E_USER: $(E2E_USER)
          E2E_PASSWORD: $(E2E_PASSWORD)      # secret variables must be mapped explicitly
      - task: PublishTestResults@2
        condition: succeededOrFailed()
        inputs:
          testResultsFormat: JUnit
          testResultsFiles: results/junit.xml
          testRunTitle: Playwright shard $(System.JobPositionInPhase)
      - task: PublishPipelineArtifact@1
        condition: succeededOrFailed()
        inputs:
          targetPath: playwright-report
          artifact: playwright-report-$(System.JobPositionInPhase)
      - task: PublishPipelineArtifact@1
        condition: failed()
        inputs:
          targetPath: test-results
          artifact: traces-$(System.JobPositionInPhase)
```
- JUnit output needs the `junit` reporter in config (see `templates/playwright.config.ts`).
- Container alternative: `container: mcr.microsoft.com/playwright:v<version>-noble` on the job, then skip `playwright install`.
- .NET projects: `dotnet build`, `pwsh bin/Release/net8.0/playwright.ps1 install --with-deps`, `dotnet test --logger trx`, publish with `testResultsFormat: VSTest`.

## Reports and artifacts
| Artifact | Where | Use |
|---|---|---|
| HTML report | `playwright-report/` | Browse results, attached traces; `npx playwright show-report <dir>` locally |
| Traces / screenshots / videos | `test-results/` | Debug failures: `npx playwright show-trace <trace.zip>` |
| JUnit XML | `results/junit.xml` | CI test tab, trend and flaky tracking |
| Blob reports | `blob-report/` | Merge shards into one report |

## Pipeline strategy
- PR: smoke/critical tag (`--grep @smoke`) on Chromium, sharded; < 10 min.
- Main / nightly: full suite, all browsers, visual tests in the Docker image.
- Track flaky tests (pass on retry) from the report; fix or quarantine with an owner and ticket (`test.fixme` with reason), never silently skip.
- Run against an ephemeral or dedicated test environment with seeded data; never against production with real customer data.
- For a local dev server use `webServer` in config (`command`, `url`, `reuseExistingServer: !process.env.CI`).
