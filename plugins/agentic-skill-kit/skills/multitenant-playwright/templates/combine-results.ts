import { parseCaseLog } from './case-log';
import { assertRecordMatchesTenant } from './cache';
import type { Cell, MatrixColumn } from './summary';

/**
 * Model B "combine" step, as pure functions: take what each tenant job produced and build the
 * latest-valid-per-tenant view. Rules proven in a real multi-tenant pipeline:
 *  - newest result wins per (tenant, case); a skipped test never overwrites a real result;
 *  - within one run the worst outcome wins;
 *  - a run recorded for another tenant is never applied (mismatched);
 *  - a partial run cannot replace the latest pointer;
 *  - the merged view is for STATUS, never a release gate.
 * OPTIONAL helper: combine-cli.ts merges ONE run's summaries and does not use this file. Use these functions
 * when you keep a longitudinal "latest per tenant" store (artifact storage or a results branch).
 */

export type Taxonomy = 'ok' | 'env-down' | 'job-failed' | 'no-results' | 'mismatched' | 'incomplete';

export interface RunRecord {
  tenantId: string;
  runId: string;
  complete: boolean;
  at: number;
  cases: Record<string, Cell>;
}

const SEVERITY: Record<Cell, number> = { skipped: 0, passed: 1, flaky: 2, failed: 3 };

export function parseRun(text: string): RunRecord | undefined {
  const lines = parseCaseLog(text);
  const first = lines[0];
  if (!first) return undefined;
  const cases: Record<string, Cell> = {};
  let at = Date.parse(first.at) || 0;
  for (const l of lines) {
    at = Math.max(at, Date.parse(l.at) || 0);
    if (l.kind !== 'test') continue;
    const key = `${l.module}: ${l.title}`;
    const prev = cases[key];
    if (!prev || SEVERITY[l.outcome] > SEVERITY[prev]) cases[key] = l.outcome; // worst outcome wins within a run
  }
  return { tenantId: first.tenantId, runId: first.runId, complete: lines.some((l) => l.kind === 'end'), at, cases };
}

export interface JobInput {
  expectedTenantId: string;
  jobStatus: 'succeeded' | 'failed' | 'skipped';
  envDown: boolean;
  caseLogText?: string;
}

export function classify(input: JobInput): { taxonomy: Taxonomy; run?: RunRecord } {
  if (input.envDown) return { taxonomy: 'env-down' };
  const run = input.caseLogText ? parseRun(input.caseLogText) : undefined;
  if (!run) return { taxonomy: input.jobStatus === 'failed' ? 'job-failed' : 'no-results' };
  try {
    assertRecordMatchesTenant(run.tenantId, input.expectedTenantId, `Run ${run.runId}`);
  } catch {
    return { taxonomy: 'mismatched' }; // listed, never applied
  }
  return { taxonomy: run.complete ? 'ok' : 'incomplete', run }; // incomplete runs still count
}

export interface Latest {
  tenantId: string;
  runId: string;
  at: number;
  cases: Record<string, { outcome: Cell; runId: string; at: number }>;
}

export function mergeLatest(prev: Latest | undefined, run: RunRecord): Latest {
  if (prev) assertRecordMatchesTenant(prev.tenantId, run.tenantId, `Latest pointer for run ${run.runId}`);
  const cases = { ...(prev?.cases ?? {}) };
  for (const [key, outcome] of Object.entries(run.cases)) {
    const old = cases[key];
    if (outcome === 'skipped' && old) continue; // skipped never overwrites
    if (old && old.at > run.at) continue; // older run never overwrites newer
    cases[key] = { outcome, runId: run.runId, at: run.at };
  }
  return { tenantId: run.tenantId, runId: run.runId, at: run.at, cases };
}

/** A one-spec debug run must not publish a green board: only a run covering at least as much replaces the pointer. */
export const canReplacePointer = (prevCaseCount: number | undefined, nextCaseCount: number): boolean =>
  prevCaseCount === undefined || nextCaseCount >= prevCaseCount;

export type Freshness = 'green' | 'amber' | 'red';
const HOUR = 3_600_000;

export function freshness(latestAt: number | undefined, now: number): Freshness {
  if (latestAt === undefined) return 'red';
  const age = now - latestAt;
  if (age <= 48 * HOUR) return 'green';
  return age <= 7 * 24 * HOUR ? 'amber' : 'red';
}

export function toColumn(tenantId: string, latest: Latest | undefined, taxonomy: Taxonomy, now: number): MatrixColumn {
  const cases: Record<string, Cell> = {};
  for (const [k, v] of Object.entries(latest?.cases ?? {})) cases[k] = v.outcome;
  return { tenantId, status: `${taxonomy} / ${freshness(latest?.at, now)}`, cases };
}
