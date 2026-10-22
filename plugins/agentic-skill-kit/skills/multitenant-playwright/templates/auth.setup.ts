import * as fs from 'node:fs';
import * as path from 'node:path';
import { test as setup } from './fixtures';
import { AUTH_TTL_MS, authStatePath, isFresh } from './cache';
import { checkTenant, usableRoles, writeDownMarker } from './preflight';

/**
 * One setup project per tenant (generated in playwright.config.ts) runs this file with that tenant.
 * It (1) preflights the tenant, so a dead environment or missing credentials FAIL that tenant only,
 * (2) logs in once per usable role and stores a tenant-keyed session with a TTL.
 * A failed setup stops that tenant's module projects, never the other tenants (continue-all).
 */
setup('preflight and authenticate', async ({ ctx, tenant, browser }) => {
  const pre = await checkTenant(tenant);
  if (!pre.ok) {
    writeDownMarker(tenant.id, pre);
    throw new Error(`Preflight failed for ${tenant.id}: ${pre.reason} (${pre.detail})`);
  }

  for (const role of usableRoles(tenant)) {
    const file = authStatePath(tenant.id, role);
    if (isFresh(file, AUTH_TTL_MS)) continue; // cached session still inside its TTL

    // A fresh context per role: roles never share cookies.
    const context = await browser.newContext({ baseURL: tenant.baseUrl, timezoneId: tenant.timezone });
    try {
      const page = await context.newPage();
      await ctx.flows.login({ ...ctx, page }, role);
      fs.mkdirSync(path.dirname(file), { recursive: true });
      await context.storageState({ path: file });
    } finally {
      await context.close();
    }
  }
});
