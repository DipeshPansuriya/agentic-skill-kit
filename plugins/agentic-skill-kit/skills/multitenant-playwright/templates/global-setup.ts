import * as fs from 'node:fs';
import * as path from 'node:path';
import type { FullConfig } from '@playwright/test';
import { REPORT_DIR } from './cache';
import { selectTenants } from './registry';

/**
 * Runs once per Playwright process, before any project.
 * Refuses to run when no tenant is selected (an empty list can never report green),
 * mints one run id, and clears stale environment-down markers from earlier runs.
 * Per-tenant preflights live in auth.setup.ts so one dead tenant does not abort the rest.
 */
export default async function globalSetup(_config: FullConfig): Promise<void> {
  const tenants = selectTenants(process.env.TENANTS); // throws on unknown id or empty selection
  process.env.RUN_ID ??= new Date().toISOString().replace(/[-:.TZ]/g, '').slice(0, 14);

  fs.mkdirSync(REPORT_DIR, { recursive: true });
  for (const f of fs.readdirSync(REPORT_DIR)) {
    if (f.startsWith('environment-down-')) fs.rmSync(path.join(REPORT_DIR, f));
  }
  console.log(`[run ${process.env.RUN_ID}] tenants: ${tenants.map((t) => t.id).join(', ')}`);
}
