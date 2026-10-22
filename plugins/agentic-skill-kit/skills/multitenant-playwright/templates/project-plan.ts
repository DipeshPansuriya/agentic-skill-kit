import { MODULES, type ModuleName, type TenantProfile } from './tenant-types';
import { projectName, SETUP_MODULE } from './project-name';

/**
 * Pure planner: which Playwright projects exist for a selection of tenants and modules.
 * playwright.config.ts maps the plan to real projects; unit tests drive it directly.
 *
 * Module switches (environment):
 *   MODULES=isolation          only these modules (setup projects always exist)
 *   EXCLUDE_MODULES=isolation  everything except these
 * Isolation specs need at least TWO tenants' sessions in one process. With one tenant selected the planner drops
 * the isolation module with a visible warning (so a one-tenant registry or job still loads); MODULES=isolation
 * with one tenant throws. Per-tenant jobs should still set EXCLUDE_MODULES=isolation explicitly.
 */
export interface PlannedProject {
  name: string;
  tenantId: string;
  module: string;
  isSetup: boolean;
  testMatch: string[];
  dependencies: string[];
}

export interface PlanOptions {
  only?: readonly string[];
  exclude?: readonly string[];
}

export const parseList = (v: string | undefined): string[] => (v ?? '').split(',').map((s) => s.trim()).filter(Boolean);

export function planProjects(
  tenants: readonly TenantProfile[],
  opts: PlanOptions = {},
  warn: (message: string) => void = (m) => console.warn(m),
): PlannedProject[] {
  const only = opts.only ?? [];
  const exclude = opts.exclude ?? [];
  for (const m of [...only, ...exclude]) {
    if (!(MODULES as readonly string[]).includes(m)) throw new Error(`Unknown module "${m}". Known: ${MODULES.join(', ')}`);
  }
  const selected = (m: ModuleName): boolean => (only.length === 0 || only.includes(m)) && !exclude.includes(m);
  const setupNames = tenants.map((t) => projectName(t.id, SETUP_MODULE));

  const plan = tenants.flatMap((t): PlannedProject[] => [
    {
      name: projectName(t.id, SETUP_MODULE),
      tenantId: t.id,
      module: SETUP_MODULE,
      isSetup: true,
      testMatch: ['**/auth.setup.ts'],
      dependencies: [],
    },
    ...MODULES.filter((m) => t.modules[m].scope === 'in' && selected(m)).map((m) => ({
      name: projectName(t.id, m),
      tenantId: t.id,
      module: m,
      isSetup: false,
      // common/<module> runs on every tenant; <tenant>/<module> is tenant-only. Specs never carry tenant names.
      testMatch: [`**/common/${m}/**/*.spec.ts`, `**/${t.id}/${m}/**/*.spec.ts`],
      // Isolation also needs the OTHER tenants' sessions, so it waits for every selected setup.
      dependencies: m === 'isolation' ? setupNames : [projectName(t.id, SETUP_MODULE)],
    })),
  ]);

  const hasIsolation = plan.some((p) => p.module === 'isolation');
  if (tenants.length < 2 && hasIsolation) {
    // An explicit request for ONLY isolation with one tenant can never prove anything: fail loud.
    if (only.includes('isolation')) {
      throw new Error('MODULES=isolation needs at least two tenants in the same run: select more tenants (TENANTS).');
    }
    // Otherwise isolation is merely part of "all modules": drop it for this one-tenant selection, visibly.
    warn(
      'isolation module not planned: a one-tenant selection cannot test isolation. ' +
        'Run it in a pass or job that selects two or more tenants (TENANTS=a,b MODULES=isolation).',
    );
    return plan.filter((p) => p.module !== 'isolation');
  }
  return plan;
}

/**
 * The extra isolation pass of a one-command Model B run (run-all.ts): per-tenant children exclude isolation,
 * then ONE pass selects every tenant. With fewer than two tenants the pass is skipped, with a visible line.
 */
export function isolationPass(tenantIds: readonly string[]): { run: boolean; line: string } {
  return tenantIds.length >= 2
    ? { run: true, line: `isolation pass: ${tenantIds.length} tenants in one process` }
    : { run: false, line: 'isolation pass SKIPPED: it needs at least two tenants (this run selected fewer)' };
}
