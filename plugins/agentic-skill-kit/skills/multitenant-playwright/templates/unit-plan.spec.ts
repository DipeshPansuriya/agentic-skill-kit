import { expect, test } from '@playwright/test';
import { isolationPass, planProjects } from './project-plan';
import { rawTenants, selectTenants } from './registry';

/** Which projects exist for a selection. Guards the one-tenant job and the dedicated isolation job. */
test.describe('project plan', () => {
  const names = (ids: string, opts = {}): string[] => planProjects(selectTenants(ids), opts, () => undefined).map((p) => p.name);

  test('REGRESSION: TENANTS=<one id> with isolation excluded yields a valid run', () => {
    const one = rawTenants()[0]?.id as string;
    const plan = names(one, { exclude: ['isolation'] });
    expect(plan.length).toBeGreaterThan(0);
    expect(plan.every((n) => n.startsWith(`${one}__`))).toBe(true);
    expect(plan.some((n) => n.endsWith('__isolation'))).toBe(false);
  });

  test('REGRESSION: a one-tenant selection loads: isolation is dropped with a visible warning, not a throw', () => {
    const one = rawTenants()[0]?.id as string;
    const warnings: string[] = [];
    const plan = planProjects(selectTenants(one), {}, (m) => warnings.push(m));
    expect(plan.some((p) => p.module === 'isolation')).toBe(false);
    expect(plan.length).toBeGreaterThan(0);
    expect(warnings.join()).toMatch(/isolation module not planned/);
  });

  test('a registry with a single tenant plans without error (migration step 1)', () => {
    const only = rawTenants().slice(0, 1);
    expect(() => planProjects(only, {}, () => undefined)).not.toThrow();
  });

  test('MODULES=isolation with one tenant is an explicit request that can prove nothing: it throws', () => {
    const one = rawTenants()[0]?.id as string;
    expect(() => names(one, { only: ['isolation'] })).toThrow(/at least two tenants/);
  });

  test('run-all isolation pass: one extra pass for two or more tenants, visibly skipped below that', () => {
    expect(isolationPass(['tenant-a', 'tenant-b']).run).toBe(true);
    const single = isolationPass(['tenant-a']);
    expect(single.run).toBe(false);
    expect(single.line).toMatch(/SKIPPED/);
  });

  test('the isolation job selects every tenant and only that module, depending on every setup', () => {
    const ids = rawTenants().map((t) => t.id).join(',');
    const plan = planProjects(selectTenants(ids), { only: ['isolation'] });
    const iso = plan.filter((p) => p.module === 'isolation');
    expect(iso).toHaveLength(rawTenants().length);
    for (const p of iso) expect(p.dependencies).toHaveLength(rawTenants().length);
    expect(plan.filter((p) => !p.isSetup && p.module !== 'isolation')).toHaveLength(0);
  });

  test('unknown module names are rejected', () => {
    expect(() => names(rawTenants().map((t) => t.id).join(','), { exclude: ['nope'] })).toThrow(/Unknown module/);
  });
});
