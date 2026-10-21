import * as fs from 'node:fs';
import * as path from 'node:path';
import { mergeSummaries, columnsFromSummary, renderMatrix, verdict, type Summary } from './summary';

/**
 * Model B "combine" job: merge the per-tenant summaries downloaded from the tenant jobs and derive the
 * pipeline result. Runs even when tenant jobs failed (always()), so a red tenant still produces a report.
 *   EXPECTED=tenant-a,tenant-b npx tsx combine-cli.ts <dir-with-results-*> [out-dir]
 * EXPECTED comes from the decide step output, never from a hand-written list. A tenant with no summary
 * (job crashed, env down before the reporter started, artifact missing) is reported as "ran nothing" and fails.
 */
const root = process.argv[2];
const out = process.argv[3] ?? 'combined';
const expected = (process.env.EXPECTED ?? '').split(',').map((s) => s.trim()).filter(Boolean);

function* summaries(dir: string): Generator<string> {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) yield* summaries(p);
    else if (e.name === 'summary.json') yield p;
  }
}

if (!root || !fs.existsSync(root)) {
  console.error('usage: EXPECTED=a,b combine-cli.ts <results-dir> [out-dir]');
  process.exit(2);
}
const parts: Summary[] = [];
for (const f of summaries(root)) {
  try {
    parts.push(JSON.parse(fs.readFileSync(f, 'utf8')) as Summary);
  } catch {
    console.error(`unreadable summary ignored: ${f}`);
  }
}
const merged = mergeSummaries(parts[0]?.runId ?? 'unknown', expected, parts);
fs.mkdirSync(out, { recursive: true });
fs.writeFileSync(path.join(out, 'summary.json'), JSON.stringify(merged, null, 2));
const md = renderMatrix(columnsFromSummary(merged));
fs.writeFileSync(path.join(out, 'summary.md'), md + '\n');
// GitHub Actions: show in the job summary. Azure DevOps: upload summary.md with ##vso[task.uploadsummary].
if (process.env.GITHUB_STEP_SUMMARY) fs.appendFileSync(process.env.GITHUB_STEP_SUMMARY, md + '\n');

const v = verdict(merged);
const problems = [...v.problems];
// NEEDS_RESULTS="tenant:success,isolation:skipped": a cancelled job (for example a job timeout) is a failure.
for (const pair of (process.env.NEEDS_RESULTS ?? '').split(',').filter(Boolean)) {
  const [job, result] = pair.split(':');
  if (result === 'cancelled') problems.push(`job group "${job}" was cancelled`);
}
console.log(v.lines.join('\n'));
if (problems.length > 0) {
  console.error(`FAILED: ${problems.join('; ')}`);
  process.exit(1);
}
