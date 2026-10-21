import * as fs from 'node:fs';
import * as path from 'node:path';
import { REPORT_DIR } from './cache';
import { verdict, type Summary } from './summary';

/**
 * CI result derived from the summary, in an always() step AFTER the test and scrub steps (which ran with
 * continue-on-error so artifacts could still publish). Exit 1 when:
 *  - the summary is missing, unreadable or empty;
 *  - Playwright's run status is not passed/failed (a global timeout or interrupt);
 *  - any expected tenant failed, ran nothing, or left a planned module unrun;
 *  - RUN_ID is set and the summary belongs to another run (stale file);
 *  - any step named in STEP_OUTCOMES did not succeed, e.g. STEP_OUTCOMES="tests:success,scrub:success".
 * In CI pass the real outcomes: STEP_OUTCOMES: tests:${{ steps.tests.outcome }},scrub:${{ steps.scrub.outcome }}
 *   npx tsx check-summary.ts [path/to/summary.json]
 */
const file = process.argv[2] ?? path.join(REPORT_DIR, 'summary.json');
let summary: Summary | undefined;
try {
  summary = JSON.parse(fs.readFileSync(file, 'utf8')) as Summary;
} catch {
  summary = undefined;
}
const v = verdict(summary, process.env.RUN_ID);
const problems = [...v.problems];
for (const pair of (process.env.STEP_OUTCOMES ?? '').split(',').filter(Boolean)) {
  const [step, outcome] = pair.split(':');
  // The test step normally "fails" when tests fail; that already shows in the summary. Anything other than
  // success on the scrub step, or a cancelled/skipped test step, must fail the job.
  if (outcome !== 'success' && (step !== 'tests' || outcome !== 'failure')) problems.push(`step "${step}" ended as "${outcome}"`);
  if (step === 'scrub' && outcome !== 'success') problems.push('artifacts were not scrubbed: they must not be published');
}
for (const line of v.lines) console.log(line);
if (problems.length > 0) {
  console.error(`FAILED: ${problems.join('; ')}`);
  process.exit(1);
}
console.log('All expected tenants passed.');
