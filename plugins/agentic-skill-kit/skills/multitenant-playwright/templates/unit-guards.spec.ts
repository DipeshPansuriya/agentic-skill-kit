
import { expect, test } from '@playwright/test';
import { deepMerge } from './/env-overlay';
import { safeSlugList } from './/project-name';
import { safeRepoRelativePath } from './/decide';
import { isSummaryShape, parseSummary, SUMMARY_MAX_BYTES } from './/summary';

test.describe('overlay hardening (no prototype pollution)', () => {
  const base = { a: 1, nested: { b: 2 } };

  test('REGRESSION: an overlay containing __proto__ cannot pollute Object.prototype', () => {
    const overlay: unknown = JSON.parse('{"__proto__": {"polluted": true}}');
    expect(() => deepMerge(base, overlay)).toThrow();
    expect(({} as Record<string, unknown>).polluted).toBeUndefined();
    expect(({} as Record<string, unknown>).constructor).not.toEqual('pwned');
  });

  test('prototype-like and array-index overlay keys are refused; unknown keys still fail loudly', () => {
    for (const key of ['constructor', 'prototype', '__PROTO__']) {
      expect(() => deepMerge(base, { [key]: { x: 1 } }), key).toThrow(/refused/);
    }
    expect(() => deepMerge(base, { '0': 1 })).toThrow(/array-index/);
    expect(() => deepMerge(base, { nope: 1 })).toThrow(/does not exist/);
    expect(deepMerge(base, { nested: { b: 3 } })).toEqual({ a: 1, nested: { b: 3 } });
  });
});

test.describe('safe slug lists', () => {
  test('REGRESSION: valid slugs pass, everything else is named and refused', () => {
    expect(safeSlugList('MODULES', 'isolation, orders')).toEqual(['isolation', 'orders']);
    expect(safeSlugList('EXCLUDE_MODULES', '')).toEqual([]);
    expect(() => safeSlugList('MODULES', 'bad_underscore')).toThrow(/MODULES entries must be safe slugs/);
    expect(() => safeSlugList('TENANTS', 'upper;case')).toThrow(/bad: upper;case/);
  });
});

test.describe('repo-relative path guard', () => {
  test('REGRESSION: traversal and absolute paths are refused with a reason', () => {
    for (const bad of ['../secrets.json', 'a/../../x.json', 'C:\\abs.json', '/abs.json', '\\\\unc\\share\\x', '']) {
      expect(safeRepoRelativePath(bad, '/repo').ok, bad).toBe(false);
    }
    expect(safeRepoRelativePath('ci/schedules.json', '/repo')).toEqual({ ok: true, path: '/repo/ci/schedules.json' });
    expect(safeRepoRelativePath('ci\\x.json', 'D:\\repo').ok).toBe(true);
  });
});

test.describe('untrusted summary parsing', () => {
  const ok = JSON.stringify({ runId: 'r1', runStatus: 'passed', startedAt: '', finishedAt: '', expected: ['tenant-a'], tenants: {} });

  test('REGRESSION: an oversized or foreign-shaped summary is rejected, a well-formed one parses', () => {
    expect(parseSummary({ size: ok.length, text: ok })?.runId).toBe('r1');
    expect(parseSummary({ size: SUMMARY_MAX_BYTES + 1, text: ok })).toBeUndefined();
    expect(parseSummary({ size: 5, text: 'not j' })).toBeUndefined();
    expect(parseSummary({ size: ok.length, text: '{"runId":1,"runStatus":"x","expected":[],"tenants":{}}' })).toBeUndefined();
    expect(parseSummary({ size: 10, text: '{"unexpected":true}' })).toBeUndefined();
    expect(isSummaryShape(undefined)).toBe(false);
  });
});
