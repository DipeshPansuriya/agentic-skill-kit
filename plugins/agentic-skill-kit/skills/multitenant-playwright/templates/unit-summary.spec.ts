import { expect, test } from '@playwright/test';
import { canReplacePointer, classify, freshness, mergeLatest, parseRun } from './combine-results';
import { buildTenantSummary, mergeSummaries, renderMatrix, verdict, type CaseResult, type Summary } from './summary';

const c = (title: string, outcome: CaseResult['outcome']): CaseResult => ({ title, module: 'orders', outcome });
const log = (tenantId: string, runId: string, lines: Array<Record<string, unknown>>): string =>
  lines.map((l) => JSON.stringify({ tenantId, runId, at: '2026-01-02T00:00:00.000Z', ...l })).join('\n');

test.describe('verdict (exit policy)', () => {
  const summary = (parts: Record<string, CaseResult[]>, expected: string[], runStatus = 'passed'): Summary => ({
    runId: 'r1',
    runStatus,
    startedAt: '2026-01-02T00:00:00Z',
    finishedAt: '2026-01-02T00:10:00Z',
    expected,
    tenants: Object.fromEntries(Object.entries(parts).map(([id, cases]) => [id, buildTenantSummary(id, cases)])),
  });

  test('all green passes; flaky counts as passed', () => {
    expect(verdict(summary({ 'tenant-a': [c('x', 'passed'), c('y', 'flaky')] }, ['tenant-a'])).ok).toBe(true);
  });

  test('one failing tenant fails the run but the others are still reported', () => {
    const v = verdict(summary({ 'tenant-a': [c('x', 'failed')], 'tenant-b': [c('x', 'passed')] }, ['tenant-a', 'tenant-b']));
    expect(v.ok).toBe(false);
    expect(v.lines).toHaveLength(2);
  });

  test('a tenant that ran nothing, or only skipped, is never green', () => {
    expect(verdict(summary({ 'tenant-a': [c('x', 'passed')] }, ['tenant-a', 'tenant-b'])).ok).toBe(false);
    expect(verdict(summary({ 'tenant-a': [c('x', 'skipped')] }, ['tenant-a'])).ok).toBe(false);
  });

  test('REGRESSION: a timed-out or interrupted run is never green, even when every finished test passed', () => {
    const cases = { 'tenant-a': [c('x', 'passed')] };
    expect(verdict(summary(cases, ['tenant-a'], 'passed')).ok).toBe(true);
    expect(verdict(summary(cases, ['tenant-a'], 'timedout')).ok).toBe(false);
    expect(verdict(summary(cases, ['tenant-a'], 'interrupted')).ok).toBe(false);
    expect(verdict(summary(cases, ['tenant-a'], 'timedout')).problems.join()).toMatch(/timed out/);
  });

  test('REGRESSION: Playwright failed outside any test (e.g. a throwing global teardown) is never green', () => {
    const allPass = { 'tenant-a': [c('x', 'passed')] };
    const v = verdict(summary(allPass, ['tenant-a'], 'failed'));
    expect(v.ok).toBe(false);
    expect(v.problems.join()).toMatch(/outside any test/);
    // when a tenant really failed, the failure is explained by that tenant, not by this rule
    expect(verdict(summary({ 'tenant-a': [c('x', 'failed')] }, ['tenant-a'], 'failed')).problems.join()).not.toMatch(/outside any test/);
  });

  test('a stale summary from another run id is rejected', () => {
    const s = summary({ 'tenant-a': [c('x', 'passed')] }, ['tenant-a']);
    expect(verdict(s, 'r1').ok).toBe(true);
    expect(verdict(s, 'r2').ok).toBe(false);
  });

  test('a planned module that reported nothing makes the tenant incomplete, not passed', () => {
    const t = buildTenantSummary('tenant-a', [c('x', 'passed')], undefined, [], ['isolation']);
    expect(t.status).toBe('incomplete');
    const s: Summary = { ...summary({}, ['tenant-a']), tenants: { 'tenant-a': t } };
    expect(verdict(s).ok).toBe(false);
  });

  test('merging: stale parts dropped, same-tenant parts combined, a bad run status wins', () => {
    const a = summary({ 'tenant-a': [c('x', 'passed')] }, ['tenant-a']);
    const iso = { ...a, tenants: { 'tenant-a': buildTenantSummary('tenant-a', [{ title: 'i', module: 'isolation', outcome: 'failed' }]) } };
    const merged = mergeSummaries('r1', ['tenant-a'], [a, iso]);
    expect(merged.tenants['tenant-a']?.cases).toHaveLength(2);
    expect(verdict(merged).ok).toBe(false);
    const stale = { ...a, runId: 'old' };
    expect(verdict(mergeSummaries('r1', ['tenant-a'], [stale], true), 'r1').ok).toBe(false);
    expect(mergeSummaries('r1', ['tenant-a'], [a, { ...a, runStatus: 'timedout' }]).runStatus).toBe('timedout');
  });

  test('a preflight marker labels the tenant instead of a plain failure', () => {
    expect(buildTenantSummary('tenant-a', [c('x', 'failed')], 'no-credentials').status).toBe('no-credentials');
    expect(buildTenantSummary('tenant-a', [c('x', 'failed')], 'env-down').status).toBe('env-down');
  });

  test('missing summary, or no expected tenants, fails', () => {
    expect(verdict(undefined).ok).toBe(false);
    expect(verdict(summary({}, [])).ok).toBe(false);
  });

  test('merging per-process summaries keeps an absent tenant absent', () => {
    const a = summary({ 'tenant-a': [c('x', 'passed')] }, ['tenant-a']);
    expect(verdict(mergeSummaries('r1', ['tenant-a', 'tenant-b'], [a])).ok).toBe(false);
  });

  test('matrix shows n/a where a tenant lacks a scenario', () => {
    const md = renderMatrix([
      { tenantId: 'tenant-a', status: 'PASSED', cases: { s1: 'passed', s2: 'flaky' } },
      { tenantId: 'tenant-b', status: 'FAILED', cases: { s1: 'failed' } },
    ]);
    expect(md).toContain('| s2 | Flaky | n/a |');
    expect(md).toContain('| s1 | Pass | Fail |');
  });
});

test.describe('combine (latest valid per tenant)', () => {
  test('failure taxonomy', () => {
    const ok = log('tenant-a', 'r1', [{ kind: 'begin' }, { kind: 'test', title: 't', module: 'm', outcome: 'passed' }, { kind: 'end' }]);
    const base = { expectedTenantId: 'tenant-a', jobStatus: 'succeeded' as const, envDown: false };
    expect(classify({ ...base, caseLogText: ok }).taxonomy).toBe('ok');
    expect(classify({ ...base, envDown: true }).taxonomy).toBe('env-down');
    expect(classify({ ...base, jobStatus: 'failed' }).taxonomy).toBe('job-failed');
    expect(classify(base).taxonomy).toBe('no-results');
    expect(classify({ ...base, expectedTenantId: 'tenant-b', caseLogText: ok }).taxonomy).toBe('mismatched');
    const killed = ok.split('\n').slice(0, 2).join('\n') + '\n{"kind":"te'; // cut mid-write
    const r = classify({ ...base, caseLogText: killed });
    expect(r.taxonomy).toBe('incomplete');
    expect(Object.keys(r.run?.cases ?? {})).toHaveLength(1); // finished tests still count
  });

  test('skipped never overwrites; worst outcome wins within a run', () => {
    const run1 = parseRun(log('tenant-a', 'r1', [{ kind: 'begin' }, { kind: 'test', title: 't', module: 'm', outcome: 'passed' }, { kind: 'end' }]));
    const run2 = parseRun(
      log('tenant-a', 'r2', [{ kind: 'begin' }, { kind: 'test', title: 't', module: 'm', outcome: 'skipped' }, { kind: 'test', title: 'u', module: 'm', outcome: 'passed' }, { kind: 'test', title: 'u', module: 'm', outcome: 'failed' }, { kind: 'end' }]),
    );
    const merged = mergeLatest(mergeLatest(undefined, run1!), run2!);
    expect(merged.cases['m: t']?.outcome).toBe('passed');
    expect(merged.cases['m: u']?.outcome).toBe('failed');
  });

  test('a partial run cannot replace the latest pointer; freshness bands', () => {
    expect(canReplacePointer(40, 3)).toBe(false);
    expect(canReplacePointer(40, 40)).toBe(true);
    const now = Date.parse('2026-01-10T00:00:00Z');
    expect(freshness(now - 3_600_000, now)).toBe('green');
    expect(freshness(now - 4 * 24 * 3_600_000, now)).toBe('amber');
    expect(freshness(undefined, now)).toBe('red');
  });
});
