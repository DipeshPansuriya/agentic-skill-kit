import * as fs from 'node:fs';
import * as path from 'node:path';
import { REPORT_DIR } from './cache';
import { verdict, type Summary } from './summary';

/**
 * CI result derived from the summary, in an always() step AFTER the test step (which ran with
 * continue-on-error so artifacts and reports still publish). Exit 1 when the summary is missing,
 * unreadable, empty, or any expected tenant failed or ran nothing.
 *   npx tsx check-summary.ts [path/to/summary.json]
 */
const file = process.argv[2] ?? path.join(REPORT_DIR, 'summary.json');
let summary: Summary | undefined;
try {
  summary = JSON.parse(fs.readFileSync(file, 'utf8')) as Summary;
} catch {
  summary = undefined;
}
const v = verdict(summary);
for (const line of v.lines) console.log(line);
if (!v.ok) {
  console.error(`FAILED: ${v.problems.join('; ')}`);
  process.exit(1);
}
console.log('All expected tenants passed.');
