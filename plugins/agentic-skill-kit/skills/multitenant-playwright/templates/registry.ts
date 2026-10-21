import { MODULES, type ModuleName, type TenantProfile } from './tenant-types';
import { applyOverlay } from './env-overlay';
import { guardTodos, listTodos } from './todo';
import { overlays, tenantA, tenantB } from './tenants.example';

/**
 * The single source for Playwright projects, the CI matrix and report columns.
 * Never hand-write a tenant list anywhere else (scripts, YAML, launchers).
 * TEST_ENV picks a named overlay; it is an environment name, not a tenant, so reading it here is safe.
 */
const RAW: readonly TenantProfile[] = applyOverlay([tenantA, tenantB], overlays, process.env.TEST_ENV);

const SLUG = /^[a-z0-9]+(-[a-z0-9]+)*$/;

/** Invariants that keep the registry honest. Runs at load and in a unit test. */
export function validateRegistry(profiles: readonly TenantProfile[]): void {
  if (profiles.length === 0) throw new Error('Tenant registry is empty: nothing to test');
  const ids = new Set<string>();
  const prefixes = new Set<string>();
  const tokens = new Set<string>();
  const once = (set: Set<string>, value: unknown, what: string): void => {
    const key = String(value);
    if (set.has(key)) throw new Error(`Duplicate ${what} "${key}"`);
    set.add(key);
  };
  for (const p of profiles) {
    if (!SLUG.test(p.id)) throw new Error(`Tenant id "${p.id}" must be a lowercase slug`);
    once(ids, p.id, 'id');
    once(prefixes, p.data.recordPrefix, 'data.recordPrefix'); // uniqueness enforced, not a comment
    once(tokens, p.ci.scheduleToken, 'ci.scheduleToken');
    try {
      new Intl.DateTimeFormat('en', { timeZone: p.timezone });
    } catch {
      throw new Error(`Tenant "${p.id}": invalid timezone "${p.timezone}"`);
    }
    for (const m of MODULES) {
      if (!p.modules[m]) throw new Error(`Tenant "${p.id}": module "${m}" has no scope entry`);
    }
    if (p.modules.isolation.scope !== 'in') throw new Error(`Tenant "${p.id}": isolation specs must always be in scope`);
  }
}

validateRegistry(RAW);

export const allTenantIds = (): string[] => RAW.map((t) => t.id);

/** Unknown id throws. There is no default tenant and no fallback. */
export function getTenant(id: string): TenantProfile {
  const raw = RAW.find((t) => t.id === id);
  if (!raw) throw new Error(`Unknown tenant "${id}". Known: ${allTenantIds().join(', ')}`);
  return guardTodos(raw, raw.id);
}

/** Parse a TENANTS-style selector ("tenant-a,tenant-b"); empty selects all. An empty result refuses to run. */
export function selectTenants(selector: string | undefined, profiles: readonly TenantProfile[] = RAW): TenantProfile[] {
  const wanted = (selector ?? '').split(',').map((s) => s.trim()).filter(Boolean);
  const chosen =
    wanted.length === 0
      ? [...profiles]
      : wanted.map((id) => {
          const hit = profiles.find((t) => t.id === id);
          if (!hit) throw new Error(`TENANTS names unknown tenant "${id}". Known: ${profiles.map((t) => t.id).join(', ')}`);
          return hit;
        });
  if (chosen.length === 0) throw new Error('No tenants selected: refusing to run');
  return chosen;
}

export const modulesInScope = (t: TenantProfile): ModuleName[] => MODULES.filter((m) => t.modules[m].scope === 'in');

/** For tools (todos CLI, scope report, contract tests): the raw, unguarded profiles. */
export const rawTenants = (): readonly TenantProfile[] => RAW;
export const todosByTenant = (): Record<string, Array<{ path: string; why: string }>> =>
  Object.fromEntries(RAW.map((t) => [t.id, listTodos(t)]));
