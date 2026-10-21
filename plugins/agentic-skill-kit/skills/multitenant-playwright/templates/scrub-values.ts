import { rawTenants } from './registry';
import { readCredential } from './preflight';
import type { Role } from './tenant-types';

/** Every credential value the registry can resolve right now (all tenants, all roles). Used by the scrubber. */
export function registryCredentialValues(): string[] {
  const out: string[] = [];
  for (const t of rawTenants()) {
    for (const role of Object.keys(t.credentials) as Role[]) {
      const c = readCredential(t.credentials[role]);
      if (c) out.push(c.user, c.password);
    }
  }
  return [...new Set(out)];
}
