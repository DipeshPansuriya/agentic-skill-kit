import { test as base, expect } from '@playwright/test';
import { getTenant } from './registry';
import { standardFlows, type TenantContext } from './flows';
import type { TenantProfile } from './tenant-types';

/**
 * The tenant is a PROJECT OPTION (set per project in playwright.config.ts) read by an option fixture.
 * It defaults to '' on purpose: a project that forgot to set it fails loudly instead of testing the wrong tenant.
 */
export interface TenantOptions {
  tenantId: string;
}

interface TenantFixtures {
  tenant: TenantProfile;
  ctx: TenantContext;
}

const RUN_ID = process.env.RUN_ID ?? Date.now().toString(36);

export const test = base.extend<TenantOptions & TenantFixtures>({
  tenantId: ['', { option: true }],

  tenant: async ({ tenantId }, use) => {
    if (!tenantId) throw new Error('No tenantId on this project: set use.tenantId in playwright.config.ts');
    await use(getTenant(tenantId)); // unknown id throws; there is no default tenant
  },

  // Fresh per test: a new object, never module-level, so tests cannot leak state into each other.
  ctx: async ({ page, tenant }, use, testInfo) => {
    const used = new Set<string>();
    let seq = 0;
    const unique = (kind: string): string => {
      const value = `${tenant.data.recordPrefix}-${kind}-${RUN_ID}-${testInfo.parallelIndex}-${testInfo.repeatEachIndex}-${seq++}`;
      if (used.has(value)) throw new Error(`Generated a duplicate value "${value}"`); // enforced, not hoped for
      used.add(value);
      return value;
    };
    await use({
      page,
      tenant,
      data: tenant.data,
      run: {},
      flows: { ...standardFlows, ...tenant.overrides },
      unique,
    });
  },
});

export { expect };
