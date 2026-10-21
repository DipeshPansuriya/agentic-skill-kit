/**
 * Pure summary logic shared by the reporter, the one-command runner, the CI check and the combine step.
 * No Playwright, no file system: every function here is unit-testable (see unit-summary.spec.ts).
 */

export type Cell = 'passed' | 'failed' | 'flaky' | 'skipped';
/** Why a tenant column is not simply green/red. */
export type TenantStatus = 'passed' | 'failed' | 'env-down' | 'no-credentials' | 'no-results' | 'incomplete';
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
  /** Modules that had tests planned for this tenant but reported no case (did not run). */
  missingModules: string[];
}

export interface Summary {
  runId: string;
  /** Playwright's own run status: passed | failed | timedout | interrupted. Anything but passed/failed is a problem. */
  runStatus: string;
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
 *  - any failure is "failed"; flaky counts as passed but is shown separately;
 *  - a tenant with a planned module that reported nothing is "incomplete", never green.
 */
export function tenantStatus(totals: Totals, marker?: DownMarker, missingModules: readonly string[] = []): TenantStatus {
  if (marker) return marker;
  if (totals.passed + totals.failed + totals.flaky === 0) return 'no-results';
  if (totals.failed > 0) return 'failed';
  return missingModules.length > 0 ? 'incomplete' : 'passed';
}

export function buildTenantSummary(
  tenantId: string,
  cases: CaseResult[],
  marker?: DownMarker,
  notes: string[] = [],
  missingModules: string[] = [],
): TenantSummary {
  const totals = totalsOf(cases);
  const extra = missingModules.length ? [`modules that did not run: ${missingModules.join(', ')}`] : [];
  return { tenantId, status: tenantStatus(totals, marker, missingModules), totals, cases, notes: [...notes, ...extra], missingModules };
}

export interface Verdict {
  ok: boolean;
  lines: string[];
  problems: string[];
}

/**
 * The exit-code decision. ok=false when ANY expected tenant failed or ran nothing, or the run itself
 * did not end as passed/failed (a global timeout or an interrupt must never read as green), or the
 * summary belongs to another run (stale file).
 */
export function verdict(summary: Summary | undefined, expectedRunId?: string): Verdict {
  if (!summary) return { ok: false, lines: [], problems: ['summary is missing: nothing was reported'] };
  const problems: string[] = [];
  if (summary.runStatus !== 'passed' && summary.runStatus !== 'failed') {
    problems.push(`run ended as "${String(summary.runStatus)}" (timed out, interrupted or unknown): results are incomplete`);
  }
  if (expectedRunId !== undefined && summary.runId !== expectedRunId) {
    problems.push(`summary is from run "${summary.runId}", expected "${expectedRunId}" (stale file)`);
  }
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
  // Playwright itself failed, yet no tenant shows a failure: the error came from outside any test
  // (a throwing global teardown, a setup hook, a reporter or config error). That is never green.
  if (summary.runStatus === 'failed') {
    const tenantFailure = Object.values(summary.tenants).some((t) => t.status !== 'passed');
    if (!tenantFailure) problems.push('run failed outside any test (for example a global teardown or setup error)');
  }
  return { ok: problems.length === 0, lines, problems };
}

/**
 * Merge per-process summaries (Model B) into one. Several parts may carry the same tenant
 * (its own job plus the isolation job): cases are combined and the status recomputed.
 * With requireSameRun, parts from another run id (stale files) are dropped.
 * An expected tenant with no part stays absent on purpose, so verdict() reports "ran nothing".
 */
export function mergeSummaries(runId: string, expected: string[], parts: readonly Summary[], requireSameRun = false): Summary {
  const used = requireSameRun ? parts.filter((p) => p.runId === runId) : parts;
  const grouped = new Map<string, TenantSummary[]>();
  for (const p of used) for (const t of Object.values(p.tenants)) grouped.set(t.tenantId, [...(grouped.get(t.tenantId) ?? []), t]);
  const tenants: Record<string, TenantSummary> = {};
  for (const [id, list] of grouped) {
    const marker = list.map((t) => t.status).find((s): s is DownMarker => s === 'env-down' || s === 'no-credentials');
    tenants[id] = buildTenantSummary(
      id,
      list.flatMap((t) => t.cases),
      marker,
      list.flatMap((t) => t.notes),
      list.flatMap((t) => t.missingModules),
    );
  }
  const statuses = used.map((p) => p.runStatus);
  const bad = statuses.find((s) => s !== 'passed' && s !== 'failed');
  const runStatus = statuses.length === 0 ? 'unknown' : (bad ?? (statuses.includes('failed') ? 'failed' : 'passed'));
  const starts = used.map((p) => p.startedAt).sort();
  const ends = used.map((p) => p.finishedAt).sort();
  return {
    runId,
    runStatus,
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
