import { expect, test } from '@playwright/test';
import { planProjects } from './project-plan';
import { rawTenants, selectTenants } from './registry';

/** Which projects exist for a selection. Guards the one-tenant job and the dedicated isolation job. */
test.describe('project plan', () => {
  const names = (ids: string, opts = {}): string[] => planProjects(selectTenants(ids), opts).map((p) => p.name);

  test('REGRESSION: TENANTS=<one id> with isolation excluded yields a valid run', () => {
    const one = rawTenants()[0]?.id as string;
    const plan = names(one, { exclude: ['isolation'] });
    expect(plan.length).toBeGreaterThan(0);
    expect(plan.every((n) => n.startsWith(`${one}__`))).toBe(true);
    expect(plan.some((n) => n.endsWith('__isolation'))).toBe(false);
  });

  test('REGRESSION: a one-tenant plan that still contains isolation refuses (never a vacuous pass)', () => {
    const one = rawTenants()[0]?.id as string;
    expect(() => names(one)).toThrow(/at least two tenants/);
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
