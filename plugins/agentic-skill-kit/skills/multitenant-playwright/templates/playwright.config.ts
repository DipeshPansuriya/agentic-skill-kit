import * as path from 'node:path';
import { defineConfig, devices, type PlaywrightTestConfig } from '@playwright/test';
import type { TenantOptions } from './fixtures';
import { selectTenants } from './registry';
import { authStatePath, REPORT_DIR } from './cache';
import { parseList, planProjects } from './project-plan';

/**
 * Projects are GENERATED from the tenant registry: one setup project plus one project per tenant x module.
 *
 *   Model A (one process, all tenants):   npx playwright test
 *   Model B per-tenant job:               TENANTS=tenant-a EXCLUDE_MODULES=isolation npx playwright test
 *   Model B isolation job (pair):         TENANTS=tenant-a,tenant-b MODULES=isolation npx playwright test
 *
 * Subset by TENANTS (and MODULES / EXCLUDE_MODULES), not by --project. The reporter judges only the projects
 * that were selected, so a --project filter also works, but TENANTS keeps credentials and setup consistent.
 * Isolation specs need two tenants in one process: a one-tenant selection drops them with a warning, and
 * MODULES=isolation with one tenant throws (project-plan.ts). Check the "[plan]" line in the output.
 *
 * Nothing here reads the tenant at module load except the selectors above, and they only decide WHICH projects
 * exist. Titles, URLs and timezone are per project, never baked in globally.
 */
const isCI = !!process.env.CI;
const tenants = selectTenants(process.env.TENANTS); // throws on unknown id; empty selection refuses to run
// Unit-only runs (UNIT=1) need no projects, so they never plan (and never trip a planner check).
// The config is also evaluated inside workers; print the planner warning once, from the runner process only.
const plan = process.env.UNIT
  ? []
  : planProjects(
      tenants,
      { only: parseList(process.env.MODULES), exclude: parseList(process.env.EXCLUDE_MODULES) },
      (m) => {
        if (!process.env.TEST_WORKER_INDEX) console.warn(`[plan] ${m}`);
      },
    );
const byId = new Map(tenants.map((t) => [t.id, t]));

type Projects = NonNullable<PlaywrightTestConfig<TenantOptions>['projects']>;

const projects: Projects = plan.map((p) => {
  const t = byId.get(p.tenantId);
  if (!t) throw new Error(`planned project for unknown tenant ${p.tenantId}`);
  return {
    name: p.name,
    testMatch: p.isSetup ? /auth\.setup\.ts/ : p.testMatch,
    metadata: { tenantId: t.id, module: p.module },
    ...(p.dependencies.length ? { dependencies: p.dependencies } : {}),
    use: {
      ...devices['Desktop Chrome'],
      tenantId: t.id,
      baseURL: t.baseUrl,
      timezoneId: t.timezone,
      // The setup project creates the session, so it has no storageState.
      ...(p.isSetup ? {} : { storageState: authStatePath(t.id, 'operator') }),
    },
  };
});

// Unit tests of pure logic (registry, plan, decide, summary) need no browser and no tenant:
//   UNIT=1 npx playwright test --project=unit
const unitProject: Projects = [{ name: 'unit', testMatch: '**/unit/**/*.spec.ts' }];

export default defineConfig<TenantOptions>({
  testDir: './tests',
  outputDir: path.join(REPORT_DIR, 'test-results'),
  globalSetup: './global-setup.ts',
  forbidOnly: isCI,
  retries: isCI ? 1 : 0, // a retry is a safety net that reports "flaky", never a fix
  // Workers are SHARED across all selected tenants in one process. Per-tenant worker limits are not
  // expressible here (Model B is the answer when a tenant has a login or rate limit).
  workers: process.env.PW_WORKERS ? Number(process.env.PW_WORKERS) : isCI ? 3 : undefined,
  fullyParallel: false, // within a file tests run in order; files spread across workers
  timeout: 120_000,
  expect: { timeout: 10_000 },
  reporter: [
    ['./summary-reporter.ts'],
    ['list'],
    ['html', { open: 'never', outputFolder: path.join(REPORT_DIR, 'html') }],
    ...(isCI ? ([['junit', { outputFile: path.join(REPORT_DIR, 'junit.xml') }]] as const) : []),
  ],
  use: {
    // In CI the scrub step deletes every .zip (traces cannot be rewritten safely), so tracing there is off;
    // locally keep traces for debugging. To keep traces in CI, add a zip rewriter to the scrubber first.
    trace: isCI ? 'off' : 'retain-on-failure',
    screenshot: 'only-on-failure',
    // Headless by default. Headed-only is an app-specific constraint, never a default.
  },
  projects: process.env.UNIT ? unitProject : projects,
});
