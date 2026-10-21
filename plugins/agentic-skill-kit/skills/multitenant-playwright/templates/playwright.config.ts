import * as path from 'node:path';
import { defineConfig, devices, type PlaywrightTestConfig } from '@playwright/test';
import type { TenantOptions } from './fixtures';
import { modulesInScope, selectTenants } from './registry';
import { authStatePath, REPORT_DIR } from './cache';
import { projectName, SETUP_MODULE } from './project-name';

/**
 * Projects are GENERATED from the tenant registry: one setup project plus one project per tenant x module.
 *
 *   Model A (one process, all tenants):   npx playwright test
 *   Model B (process per tenant):         TENANTS=tenant-a npx playwright test   (the pipeline sets one id per job)
 *   Subset:                               TENANTS=tenant-a,tenant-b npx playwright test
 *
 * The same file serves both models, which is what makes the A -> B migration a pipeline change only.
 * Nothing in this file reads the tenant at module load except the TENANTS selector, and it only
 * decides WHICH projects exist. Titles, URLs and timezone are per project, never baked in globally.
 */
const isCI = !!process.env.CI;
const tenants = selectTenants(process.env.TENANTS); // throws on unknown id; empty selection refuses to run
const setupNames = tenants.map((t) => projectName(t.id, SETUP_MODULE));

type Projects = NonNullable<PlaywrightTestConfig<TenantOptions>['projects']>;

const projects: Projects = tenants.flatMap((t) => {
  const common = {
    ...devices['Desktop Chrome'],
    tenantId: t.id,
    baseURL: t.baseUrl,
    timezoneId: t.timezone,
  };
  return [
    {
      name: projectName(t.id, SETUP_MODULE),
      testMatch: /auth\.setup\.ts/,
      metadata: { tenantId: t.id, module: SETUP_MODULE },
      use: common, // no storageState: this project creates it
    },
    ...modulesInScope(t).map((m) => ({
      name: projectName(t.id, m),
      // common/<module> runs on every tenant; <tenant>/<module> is tenant-only. Specs never carry tenant names.
      testMatch: [`**/common/${m}/**/*.spec.ts`, `**/${t.id}/${m}/**/*.spec.ts`],
      metadata: { tenantId: t.id, module: m },
      // Isolation specs also need the OTHER tenants' sessions, so they wait for every selected setup.
      dependencies: m === 'isolation' ? setupNames : [projectName(t.id, SETUP_MODULE)],
      use: { ...common, storageState: authStatePath(t.id, 'operator') },
    })),
  ];
});

// Unit tests of pure logic (registry, decide, summary) need no browser and no tenant:
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
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    // Headless by default. Headed-only is an app-specific constraint, never a default.
  },
  projects: process.env.UNIT ? unitProject : projects,
});
