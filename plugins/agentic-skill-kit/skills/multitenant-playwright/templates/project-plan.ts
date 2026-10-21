import { MODULES, type ModuleName, type TenantProfile } from './tenant-types';
import { projectName, SETUP_MODULE } from './project-name';

/**
 * Pure planner: which Playwright projects exist for a selection of tenants and modules.
 * playwright.config.ts maps the plan to real projects; unit tests drive it directly.
 *
 * Module switches (environment):
 *   MODULES=isolation          only these modules (setup projects always exist)
 *   EXCLUDE_MODULES=isolation  everything except these
 * Isolation specs need at least TWO tenants' sessions in one process, so a one-tenant run must exclude them;
 * the planner refuses a one-tenant plan that still contains isolation (fail loud, never a vacuous pass).
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

export function planProjects(tenants: readonly TenantProfile[], opts: PlanOptions = {}): PlannedProject[] {
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

  if (tenants.length < 2 && plan.some((p) => p.module === 'isolation')) {
    throw new Error(
      'Isolation specs need at least two tenants in the same run. Select more tenants (TENANTS), ' +
        'or exclude the module for per-tenant jobs (EXCLUDE_MODULES=isolation) and run it in the dedicated isolation job.',
    );
  }
  return plan;
}
