import { spawn } from 'node:child_process';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { REPORT_DIR } from './cache';
import { isolationPass } from './project-plan';
import { selectTenants } from './registry';
import { columnsFromSummary, mergeSummaries, renderMatrix, verdict, type Summary } from './summary';

/**
 * RUN POLICY for Model B (process per tenant), as ONE command:
 *   npx tsx run-all.ts [--parallel N] [--fail-fast] [-- <extra playwright args>]
 *
 *  - ONE command completes ALL selected tenants (TENANTS narrows the set; empty selection refuses to run).
 *  - A failing tenant never stops the others (continue-all). --fail-fast is opt-in and only stops LAUNCHING more.
 *  - A per-tenant pass/fail summary is printed at the end.
 *  - Exit code is non-zero if any tenant failed, crashed, or ran nothing.
 * Model A needs none of this: one Playwright process already runs every project and summary-reporter.ts
 * applies the same exit policy.
 */
function flag(name: string): boolean {
  return process.argv.includes(`--${name}`);
}
function value(name: string, fallback: string): string {
  const i = process.argv.indexOf(`--${name}`);
  return i >= 0 && process.argv[i + 1] ? String(process.argv[i + 1]) : fallback;
}

const sep = process.argv.indexOf('--');
const passthrough = sep >= 0 ? process.argv.slice(sep + 1) : [];
if (passthrough.some((a) => a.startsWith('--reporter'))) {
  // A CLI reporter REPLACES the configured ones; without summary-reporter.ts no tenant can be judged.
  console.error('Do not pass --reporter: it would remove summary-reporter.ts. Configure reporters in playwright.config.ts.');
  process.exit(2);
}

/** One Playwright child. `label` names its report folder; `selection` is the TENANTS value; `modules` the module switches. */
function runOne(
  label: string,
  selection: string,
  modules: { MODULES: string; EXCLUDE_MODULES: string },
  runId: string,
): Promise<{ tenantId: string; code: number }> {
  return new Promise((resolve) => {
    const child = spawn('npx', ['playwright', 'test', ...passthrough], {
      stdio: 'inherit',
      shell: process.platform === 'win32', // npx is npx.cmd on Windows
      env: {
        ...process.env,
        ...modules,
        TENANTS: selection,
        RUN_ID: runId,
        REPORT_DIR: path.join(REPORT_DIR, label), // per-process output: parallel children never share a file
      },
    });
    child.on('error', () => resolve({ tenantId: label, code: 1 }));
    child.on('close', (code) => resolve({ tenantId: label, code: code ?? 1 }));
  });
}

async function main(): Promise<number> {
  const tenants = selectTenants(process.env.TENANTS); // throws on unknown / empty: refuses to run
  const expected = tenants.map((t) => t.id);
  const runId = process.env.RUN_ID ?? new Date().toISOString().replace(/[-:.TZ]/g, '').slice(0, 14);
  const parallelText = value('parallel', '1');
  if (!/^[1-9]\d*$/.test(parallelText)) {
    // NaN here used to start zero workers, run nothing, and then read the PREVIOUS run's summary.
    console.error(`--parallel must be a positive integer, got "${parallelText}"`);
    return 2;
  }
  const parallel = Number(parallelText);
  const failFast = flag('fail-fast');
  // A summary left by an earlier run must never be read as this run's result.
  for (const id of expected) fs.rmSync(path.join(REPORT_DIR, id, 'summary.json'), { force: true });

  const queue = [...expected];
  const crashed: string[] = [];
  let stop = false;

  const worker = async (): Promise<void> => {
    for (let id = queue.shift(); id !== undefined && !stop; id = queue.shift()) {
      // Per-tenant children never run isolation: it needs two tenants' sessions in one process.
      const r = await runOne(id, id, { MODULES: '', EXCLUDE_MODULES: 'isolation' }, runId);
      if (r.code !== 0) {
        crashed.push(id); // non-zero child exit: counted even if its summary looks fine
        if (failFast) stop = true;
      }
    }
  };
  await Promise.all(Array.from({ length: Math.min(parallel, expected.length) }, worker));

  // ONE extra pass runs isolation with every selected tenant in a single process (skipped visibly below 2 tenants).
  const iso = isolationPass(expected);
  console.log(iso.line);
  const labels = [...expected];
  if (iso.run && !stop) {
    fs.rmSync(path.join(REPORT_DIR, 'isolation', 'summary.json'), { force: true });
    const r = await runOne('isolation', expected.join(','), { MODULES: 'isolation', EXCLUDE_MODULES: '' }, runId);
    if (r.code !== 0) crashed.push('isolation');
    labels.push('isolation');
  }

  const parts: Summary[] = [];
  for (const id of labels) {
    const file = path.join(REPORT_DIR, id, 'summary.json');
    try {
      parts.push(JSON.parse(fs.readFileSync(file, 'utf8')) as Summary);
    } catch {
      // missing or unreadable: the tenant stays absent and verdict() reports "ran nothing"
    }
  }
  const merged = mergeSummaries(runId, expected, parts, true); // drops parts from another run id
  fs.mkdirSync(REPORT_DIR, { recursive: true });
  fs.writeFileSync(path.join(REPORT_DIR, 'summary.json'), JSON.stringify(merged, null, 2));
  fs.writeFileSync(path.join(REPORT_DIR, 'summary.md'), renderMatrix(columnsFromSummary(merged)) + '\n');

  const v = verdict(merged, runId);
  console.log(`\n=== Per-tenant result (run ${runId}) ===\n${v.lines.join('\n')}`);
  const notRun = failFast && stop ? queue : [];
  if (notRun.length) console.log(`Not started because of --fail-fast: ${notRun.join(', ')}`);
  if (crashed.length) console.log(`Non-zero exit from: ${crashed.join(', ')}`);
  if (!v.ok) console.log(`Problems: ${v.problems.join('; ')}`);
  return v.ok && crashed.length === 0 && notRun.length === 0 ? 0 : 1;
}

main().then(
  (code) => process.exit(code),
  (e: unknown) => {
    console.error(e instanceof Error ? e.message : String(e));
    process.exit(1);
  },
);
