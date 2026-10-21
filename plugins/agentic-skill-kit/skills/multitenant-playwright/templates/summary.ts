/**
 * Pure summary logic shared by the reporter, the one-command runner, the CI check and the combine step.
 * No Playwright, no file system: every function here is unit-testable (see summary.spec.ts).
 */

export type Cell = 'passed' | 'failed' | 'flaky' | 'skipped';
/** Why a tenant column is not simply green/red. */
export type TenantStatus = 'passed' | 'failed' | 'env-down' | 'no-credentials' | 'no-results';
/** Written by the tenant preflight (preflight.ts). */
export type DownMarker = 'env-down' | 'no-credentials';

export interface CaseResult {
  title: string;
  module: string;
  outcome: Cell;
  /** First line of the error, ANSI stripped. */
  error?: string;
}

export interface Totals {
  passed: number;
  failed: number;
  flaky: number;
  skipped: number;
}

export interface TenantSummary {
  tenantId: string;
  status: TenantStatus;
  totals: Totals;
  cases: CaseResult[];
  notes: string[];
}

export interface Summary {
  runId: string;
  startedAt: string;
  finishedAt: string;
  /** Tenants the run was ASKED to cover. A tenant listed here but absent from `tenants` ran nothing. */
  expected: string[];
  tenants: Record<string, TenantSummary>;
}

export const emptyTotals = (): Totals => ({ passed: 0, failed: 0, flaky: 0, skipped: 0 });

export function totalsOf(cases: readonly { outcome: Cell }[]): Totals {
  const t = emptyTotals();
  for (const c of cases) t[c.outcome] += 1;
  return t;
}

/**
 * Status rules (the anti-false-green core):
 *  - a preflight marker (environment down, or no usable login) wins;
 *  - nothing executed (all skipped, or no cases at all) is "no-results", never green;
 *  - any failure is "failed"; flaky counts as passed but is shown separately.
 */
export function tenantStatus(totals: Totals, marker?: DownMarker): TenantStatus {
  if (marker) return marker;
  if (totals.passed + totals.failed + totals.flaky === 0) return 'no-results';
  return totals.failed > 0 ? 'failed' : 'passed';
}

export function buildTenantSummary(tenantId: string, cases: CaseResult[], marker?: DownMarker, notes: string[] = []): TenantSummary {
  const totals = totalsOf(cases);
  return { tenantId, status: tenantStatus(totals, marker), totals, cases, notes };
}

export interface Verdict {
  ok: boolean;
  lines: string[];
  problems: string[];
}

/** The exit-code decision. Non-zero (ok=false) when ANY expected tenant failed or ran nothing. */
export function verdict(summary: Summary | undefined): Verdict {
  if (!summary) return { ok: false, lines: [], problems: ['summary is missing: nothing was reported'] };
  const problems: string[] = [];
  if (summary.expected.length === 0) problems.push('no tenants were expected: an empty run is not a pass');
  const lines: string[] = [];
  for (const id of summary.expected) {
    const t = summary.tenants[id];
    if (!t) {
      problems.push(`${id}: ran nothing`);
      lines.push(`${id.padEnd(16)} NO-RESULTS  (tenant produced no summary)`);
      continue;
    }
    const x = t.totals;
    lines.push(
      `${id.padEnd(16)} ${t.status.toUpperCase().padEnd(11)} pass ${x.passed}  fail ${x.failed}  flaky ${x.flaky}  skipped ${x.skipped}`,
    );
    if (t.status !== 'passed') problems.push(`${id}: ${t.status}`);
  }
  return { ok: problems.length === 0, lines, problems };
}

/** Merge per-process summaries (Model B) into one. Expected tenants with no part stay missing on purpose. */
export function mergeSummaries(runId: string, expected: string[], parts: readonly Summary[]): Summary {
  const tenants: Record<string, TenantSummary> = {};
  for (const p of parts) Object.assign(tenants, p.tenants);
  const starts = parts.map((p) => p.startedAt).sort();
  const ends = parts.map((p) => p.finishedAt).sort();
  return {
    runId,
    expected,
    tenants,
    startedAt: starts[0] ?? new Date(0).toISOString(),
    finishedAt: ends[ends.length - 1] ?? new Date(0).toISOString(),
  };
}

const LABEL: Record<Cell, string> = { passed: 'Pass', failed: 'Fail', flaky: 'Flaky', skipped: 'Skipped' };

export interface MatrixColumn {
  tenantId: string;
  /** Free text under the tenant name, e.g. "FAILED" or "stale 3d". */
  status: string;
  /** title -> outcome; a title the tenant does not have is shown as n/a. */
  cases: Record<string, Cell>;
}

/** Markdown matrix: rows = scenario title, columns = tenants, plus a totals row per tenant. */
export function renderMatrix(columns: readonly MatrixColumn[]): string {
  const titles = [...new Set(columns.flatMap((c) => Object.keys(c.cases)))].sort();
  const head = `| Scenario | ${columns.map((c) => c.tenantId).join(' | ')} |`;
  const sep = `|---|${columns.map(() => '---').join('|')}|`;
  const rows = titles.map((t) => `| ${t.replace(/\|/g, '\\|')} | ${columns.map((c) => (c.cases[t] ? LABEL[c.cases[t]] : 'n/a')).join(' | ')} |`);
  const total = (c: MatrixColumn): string => {
    const x = totalsOf(Object.values(c.cases).map((outcome) => ({ outcome })));
    return `${x.passed + x.flaky}/${x.passed + x.flaky + x.failed} (flaky ${x.flaky}, skipped ${x.skipped})`;
  };
  return [head, sep, ...rows, `| **Totals** | ${columns.map(total).join(' | ')} |`, `| **Status** | ${columns.map((c) => c.status).join(' | ')} |`].join('\n');
}

export function columnsFromSummary(summary: Summary): MatrixColumn[] {
  return summary.expected.map((id) => {
    const t = summary.tenants[id];
    const cases: Record<string, Cell> = {};
    for (const c of t?.cases ?? []) cases[`${c.module}: ${c.title}`] = c.outcome;
    return { tenantId: id, status: (t?.status ?? 'no-results').toUpperCase(), cases };
  });
}
