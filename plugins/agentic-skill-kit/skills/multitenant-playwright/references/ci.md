# CI

Sketches are GitHub Actions syntax; the structure is vendor-neutral. Files: `templates/pipeline-model-a.yml`, `templates/pipeline-model-b.yml`, `templates/pipeline-pr.yml`, `templates/decide.ts`, `templates/decide-cli.ts`, `templates/combine-cli.ts`, `templates/check-summary.ts`.

## Shape per model
**Model A** (one job): install, unit tests (`UNIT=1 npx playwright test --project=unit`), write the credentials file, `npx playwright test` with continue-on-error, scrub, publish artifacts, remove the credentials file, then derive the result with `check-summary.ts`.

**Model B** (three stages):
1. `decide`: `decide-cli.ts` reads the registry, picks tenants by schedule token or manual selection, emits `matrix` and the expected `tenants` list. It fails when nothing is selected.
2. `tenant` jobs: one per matrix entry, `TENANTS` and `REPORT_DIR` per job, `fail-fast: false`, timeout from the registry, own credentials secret, same steps as Model A, result from that tenant's summary.
3. `combine`: runs when decide succeeded (`always()`), downloads every tenant's artifact, runs `combine-cli.ts` with `EXPECTED` from decide; a tenant with no artifact fails the pipeline. Publishes the matrix to the job summary.

## Equivalents
| Concept | GitHub Actions | Azure DevOps |
|---|---|---|
| Schedule + manual | `schedule`, `workflow_dispatch` | `schedules:` with `displayName`, manual run parameters |
| Schedule name for decide | cron string only (map cron to a name in a data file, or one workflow per schedule) | `Build.CronSchedule.DisplayName` |
| Dynamic matrix | `strategy.matrix: ${{ fromJSON(needs.decide.outputs.matrix) }}` | `strategy: matrix: $[ dependencies.decide.outputs['stepName.matrix'] ]`, output set with `##vso[task.setvariable ...;isOutput=true]` (`--format azure`) |
| Job per tenant, never fail-fast | `fail-fast: false` | jobs are independent; do not use `dependsOn` between tenants |
| Continue then publish | `continue-on-error: true` + `if: always()` | `continueOnError: true` + `condition: always()` |
| Secrets | `secrets.NAME` (dynamic lookup `secrets[matrix.name]`: **verify**) | variable group per tenant mapped via `env:` |
| Artifacts | `actions/upload-artifact` | `PublishPipelineArtifact`, `PublishTestResults` (JUnit) |
| Summary page | `$GITHUB_STEP_SUMMARY` | `##vso[task.uploadsummary]` |
| Start/stop a dedicated agent | job with `needs`, stop job `if: always()` | server job starts the VM, stop job `condition: always()` |

## The decide script
`decide()` is a pure function (`templates/decide.ts`): input is the reason, the schedule name or manual flags, and the tenant list; output is the chosen tenants. It never reads files or the environment.
- Schedule: a tenant is selected when its `scheduleToken` appears as a whole word in the schedule name ("nightly-a" must not match "nightly-ab").
- Manual: flags by tenant id; unknown ids throw.
- **Fails instead of skipping**: no tenant selected is an error, so a mistyped schedule can never produce a silent green.
Contract tests drive it with the real registry (`templates/unit-decide.spec.ts`): whole-word match, unknown id, empty selection, and the pipeline file itself (no tenant id written into it, no literal secret assignment, file present).

## PR pipeline (`templates/pipeline-pr.yml`)
Never touches a live environment, needs no secrets: typecheck, architecture lint with ratchet, unit and contract tests, `npx playwright test --list` (proves projects generate for every tenant without a browser or network), and the todo report. A PR cannot reach the nightly run without passing the registry and pipeline contract.

## Results
Publish results as artifacts (or to a results branch/storage), **not** by committing to the main branch from CI. A reviewed pipeline committed combined results to main from CI; it needed a branch-policy bypass for the build identity, added noise to history and could race.

## Triggers and policy
- Scheduled and manual only for live environments; no PR trigger on them.
- Booking-like specs consume real slots and credits: gate them per tenant with a data-driven policy and run window (for example `always` vs `full-only`, window evaluated in the tenant's zone via `Intl.DateTimeFormat`), not by tribal knowledge.
- Per-tenant run lists as data (`ci/in-scope/<tenant>.json`) with a drift gate (listed-but-missing, in-both-lists, pass naming a spec not in scope) are optional; strict in PR and local runs, a warning in the nightly. A spec for the wrong tenant once cost another tenant two nights.
- Wall time: set a per-tenant timeout from the registry; the longest observed run was 176 min against a 240 min cap.

## Adding a tenant must be one edit
If a new tenant needs YAML parameters, a template call, `dependsOn` and `--job` edits, the matrix is hand-written. Derive it from the registry, then add the contract test that proves it.
