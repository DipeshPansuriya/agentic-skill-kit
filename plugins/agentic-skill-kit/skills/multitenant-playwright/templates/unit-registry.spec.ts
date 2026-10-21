import { expect, test } from '@playwright/test';
import { applyOverlay, deepMerge } from './env-overlay';
import { parseProjectName, projectName } from './project-name';
import { allTenantIds, getTenant, rawTenants, selectTenants, validateRegistry } from './registry';
import { guardTodos, listTodos, todo } from './todo';
import { readCredential } from './preflight';
import { tenantA } from './tenants.example';
import type { CredentialRef } from './tenant-types';

/** Unit tests of pure logic, run by the Playwright runner (project "unit"; no browser needed). */
const refOf = (userVar: string, passwordVar: string): CredentialRef => ({ userVar, passwordVar });

test.describe('registry', () => {
  test('is valid and ids are unique slugs', () => {
    expect(() => validateRegistry(rawTenants())).not.toThrow();
    expect(new Set(allTenantIds()).size).toBe(allTenantIds().length);
  });

  test('unknown tenant has no fallback', () => {
    expect(() => getTenant('nope')).toThrow(/Unknown tenant/);
    expect(() => selectTenants('nope')).toThrow(/unknown tenant/);
  });

  test('an empty registry refuses to run', () => {
    expect(() => validateRegistry([])).toThrow(/empty/);
    expect(() => selectTenants('', [])).toThrow(/refusing to run/);
  });

  test('duplicate record prefix is rejected (uniqueness is enforced, not a comment)', () => {
    const clone = structuredClone(tenantA); // same record prefix as tenantA on purpose
    const otherSchedule = 'nightly-z';
    clone.id = 'tenant-z';
    clone.ci.scheduleToken = otherSchedule;
    expect(() => validateRegistry([tenantA, clone])).toThrow(/Duplicate data.recordPrefix/);
  });
});

test.describe('todo placeholders', () => {
  test('reading an unfilled value throws, naming tenant and path; siblings stay readable', () => {
    const guarded = guardTodos({ data: { phone: todo('ask admin'), code: 'X1' } }, 'tenant-q');
    expect(guarded.data.code).toBe('X1');
    expect(() => guarded.data.phone).toThrow(/tenant-q.*data\.phone.*ask admin/);
  });

  test('listTodos finds them on the raw profile', () => {
    expect(listTodos({ a: { b: todo('why') } })).toEqual([{ path: 'a.b', why: 'why' }]);
  });
});

test.describe('environment overlay', () => {
  test('deep-merges objects and replaces arrays', () => {
    expect(deepMerge({ a: { b: 1, c: 2 }, d: [1, 2] }, { a: { b: 9 }, d: [3] })).toEqual({ a: { b: 9, c: 2 }, d: [3] });
  });

  test('unknown profile, unknown tenant and unknown key all throw', () => {
    const base = [{ id: 'tenant-a', url: 'x' }];
    expect(() => applyOverlay(base, { staging: {} }, 'prod')).toThrow(/Unknown environment/);
    expect(() => applyOverlay(base, { staging: { 'tenant-q': {} } }, 'staging')).toThrow(/unknown tenant/);
    expect(() => applyOverlay(base, { staging: { 'tenant-a': { urll: 'y' } } }, 'staging')).toThrow(/does not exist/);
  });
});

test.describe('project names and credentials', () => {
  test('round-trip tenant and module', () => {
    expect(parseProjectName(projectName('tenant-a', 'orders'))).toEqual({ tenantId: 'tenant-a', module: 'orders' });
    expect(parseProjectName('chromium')).toBeUndefined();
  });

  test('a placeholder credential counts as unusable', () => {
    const placeholder = 'CHANGE_ME';
    process.env.TEST_UNIT_USER = placeholder;
    process.env.TEST_UNIT_PASS = placeholder;
    expect(readCredential(refOf('TEST_UNIT_USER', 'TEST_UNIT_PASS'))).toBeUndefined();
    expect(readCredential(refOf('TEST_UNIT_MISSING', 'TEST_UNIT_PASS'))).toBeUndefined();
  });
});
