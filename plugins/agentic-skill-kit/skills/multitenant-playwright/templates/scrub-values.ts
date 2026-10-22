import { rawTenants } from './registry';
import { readCredential } from './preflight';
import type { Role } from './tenant-types';

/** Every (user, password) pair the registry can resolve right now (all tenants, all roles). Used by the scrubber. */
export function registryCredentialPairs(): Array<[string, string]> {
  const out: Array<[string, string]> = [];
  for (const t of rawTenants()) {
    for (const role of Object.keys(t.credentials) as Role[]) {
      const c = readCredential(t.credentials[role]);
      if (c) out.push([c.user, c.password]);
    }
  }
  return out;
}

/** Flat list of distinct values. */
export const registryCredentialValues = (): string[] => [...new Set(registryCredentialPairs().flatMap(([u, p]) => [u, p]))];
