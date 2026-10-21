import * as fs from 'node:fs';
import * as path from 'node:path';
import type { FullConfig, FullResult, Reporter, Suite, TestCase, TestResult } from '@playwright/test/reporter';
import { appendCaseLine } from './case-log';
import { REPORT_DIR } from './cache';
import { parseProjectName, SETUP_MODULE } from './project-name';
import {
  buildTenantSummary,
  columnsFromSummary,
  renderMatrix,
  verdict,
  type Cell,
  type CaseResult,
  type DownMarker,
  type Summary,
} from './summary';

/**
 * Tenant-aware summary reporter.
 *  - Derives tenant and module from the PROJECT NAME (project-name.ts), so a new tenant needs no change here.
 *  - Never throws: a reporting bug must not turn a green run red or hide a red one.
 *  - Does nothing under --list or when no tenant project exists (unit-only runs).
 *  - Appends each finished test to a per-tenant case log immediately (kill-resilient).
 *  - A tenant that ran nothing, or whose environment is down, makes the run FAIL even if Playwright says passed.
 */
// eslint-disable-next-line no-control-regex
const ANSI = /\u001b\[[0-9;]*m/g;

class SummaryReporter implements Reporter {
  private readonly disabled = process.argv.includes('--list');
  private runId = process.env.RUN_ID ?? new Date().toISOString().replace(/[-:.TZ]/g, '').slice(0, 14);
  private startedAt = new Date().toISOString();
  private expected: string[] = [];
  private readonly cases = new Map<string, CaseResult[]>();

  onBegin(config: FullConfig, _suite: Suite): void {
    this.safely(() => {
      this.runId = process.env.RUN_ID ?? this.runId;
      const ids = config.projects.map((p) => parseProjectName(p.name)?.tenantId).filter((x): x is string => !!x);
      this.expected = [...new Set(ids)];
      for (const id of this.expected) {
        this.cases.set(id, []);
        if (!this.disabled) appendCaseLine({ kind: 'begin', tenantId: id, runId: this.runId, at: new Date().toISOString() });
      }
    });
  }

  onTestEnd(test: TestCase, result: TestResult): void {
    this.safely(() => {
      if (this.disabled) return;
      const isFinal = result.status === 'passed' || result.status === 'skipped' || result.retry >= test.retries;
      if (!isFinal) return; // an earlier attempt that will be retried
      const name = test.parent.project()?.name;
      const parsed = name ? parseProjectName(name) : undefined;
      if (!parsed) return;
      const outcome = toCell(test.outcome());
      const error = result.error?.message?.replace(ANSI, '').split('\n')[0];
      const item: CaseResult = { title: test.title, module: parsed.module, outcome, ...(error ? { error } : {}) };
      // A passing setup is not a test result: it must never make a tenant look "ran something".
      if (!(parsed.module === SETUP_MODULE && outcome === 'passed')) this.cases.get(parsed.tenantId)?.push(item);
      appendCaseLine({
        kind: 'test',
        tenantId: parsed.tenantId,
        runId: this.runId,
        title: test.title,
        module: parsed.module,
        outcome,
        at: new Date().toISOString(),
      });
    });
  }

  async onEnd(result: FullResult): Promise<{ status?: FullResult['status'] } | undefined> {
    try {
      const executed = [...this.cases.values()].some((c) => c.length > 0);
      if (this.disabled || this.expected.length === 0 || !executed) {
        if (!this.disabled && this.expected.length > 0) console.error('[summary] no test results were recorded for any tenant');
        return !this.disabled && this.expected.length > 0 && result.status === 'passed' ? { status: 'failed' } : undefined;
      }
      const summary: Summary = {
        runId: this.runId,
        startedAt: this.startedAt,
        finishedAt: new Date().toISOString(),
        expected: this.expected,
        tenants: {},
      };
      for (const id of this.expected) {
        const list = this.cases.get(id) ?? [];
        if (list.length === 0) continue; // ran nothing: stays absent so verdict() reports it
        const marker = readMarker(id);
        const setupFailed = list.some((c) => c.module === SETUP_MODULE && c.outcome === 'failed');
        const notes = setupFailed ? ['setup failed: this tenant\'s module projects did not run'] : [];
        summary.tenants[id] = buildTenantSummary(id, list, marker, notes);
      }
      fs.mkdirSync(REPORT_DIR, { recursive: true });
      fs.writeFileSync(path.join(REPORT_DIR, 'summary.json'), JSON.stringify(summary, null, 2));
      fs.writeFileSync(path.join(REPORT_DIR, 'summary.md'), renderMatrix(columnsFromSummary(summary)) + '\n');
      for (const id of this.expected) appendCaseLine({ kind: 'end', tenantId: id, runId: this.runId, at: new Date().toISOString() });

      const v = verdict(summary);
      console.log(`\nPer-tenant result (run ${this.runId})\n${v.lines.join('\n')}`);
      if (!v.ok) console.log(`Problems: ${v.problems.join('; ')}`);
      return !v.ok && result.status === 'passed' ? { status: 'failed' } : undefined;
    } catch (e) {
      console.error(`[summary] reporter error (ignored): ${e instanceof Error ? e.message : String(e)}`);
      return undefined;
    }
  }

  printsToStdio(): boolean {
    return true;
  }

  private safely(fn: () => void): void {
    try {
      fn();
    } catch (e) {
      console.error(`[summary] reporter error (ignored): ${e instanceof Error ? e.message : String(e)}`);
    }
  }
}

/** Reads the preflight marker written by preflight.ts, if any. Never throws. */
function readMarker(tenantId: string): DownMarker | undefined {
  try {
    const file = path.join(REPORT_DIR, `environment-down-${tenantId}.json`);
    if (!fs.existsSync(file)) return undefined;
    const reason = (JSON.parse(fs.readFileSync(file, 'utf8')) as { reason?: string }).reason;
    return reason === 'no-credentials' ? 'no-credentials' : 'env-down';
  } catch {
    return 'env-down';
  }
}

function toCell(outcome: ReturnType<TestCase['outcome']>): Cell {
  switch (outcome) {
    case 'expected':
      return 'passed';
    case 'flaky':
      return 'flaky';
    case 'skipped':
      return 'skipped';
    default:
      return 'failed';
  }
}

export default SummaryReporter;
