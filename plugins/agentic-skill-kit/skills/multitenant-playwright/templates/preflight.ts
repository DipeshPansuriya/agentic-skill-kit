import * as fs from 'node:fs';
import * as path from 'node:path';
import { REPORT_DIR } from './cache';
import type { CredentialRef, Role, TenantProfile } from './tenant-types';

/**
 * Preflights: make "nothing ran", "no usable credentials" and "environment down" impossible to report green.
 * Secrets come ONLY from environment variables (filled from the secret store / variable group) or from a
 * credentials file the pipeline writes at job start and deletes in an always() step. Never from the repo.
 */

/** A template full of placeholders counts as unusable. */
const PLACEHOLDER = /^(|change[_-]?me|replace[_-]?me|todo|tbd|x{3,}|\*+|<[^>]*>)$/i;

let fileCache: Record<string, string> | undefined;
function fromFile(name: string): string | undefined {
  const file = process.env.CREDENTIALS_FILE;
  if (!file) return undefined;
  fileCache ??= JSON.parse(fs.readFileSync(file, 'utf8')) as Record<string, string>;
  return fileCache[name];
}

const lookup = (name: string): string | undefined => process.env[name] ?? fromFile(name);

export interface Credential {
  user: string;
  password: string;
}

export function readCredential(ref: CredentialRef | undefined): Credential | undefined {
  if (!ref) return undefined;
  const user = lookup(ref.userVar);
  const password = lookup(ref.passwordVar);
  if (user === undefined || password === undefined) return undefined;
  if (PLACEHOLDER.test(user.trim()) || PLACEHOLDER.test(password.trim())) return undefined;
  return { user, password };
}

export function requireCredential(tenant: TenantProfile, role: Role): Credential {
  const cred = readCredential(tenant.credentials[role]);
  if (!cred) throw new Error(`Tenant "${tenant.id}": no usable credential for role "${role}" (missing or placeholder)`);
  return cred;
}

export const usableRoles = (tenant: TenantProfile): Role[] =>
  (Object.keys(tenant.credentials) as Role[]).filter((r) => readCredential(tenant.credentials[r]) !== undefined);

export type PreflightResult = { ok: true } | { ok: false; reason: 'no-credentials' | 'env-down'; detail: string };

const sleep = (ms: number): Promise<void> => new Promise((r) => setTimeout(r, ms));

/** Probe the tenant's base URL. Retries transient failures only (network error, 5xx); 4xx means the host is up. */
export async function probe(url: string, attempts = 3, timeoutMs = 10_000): Promise<{ up: boolean; detail: string }> {
  let detail = 'no attempt made';
  for (let i = 1; i <= attempts; i++) {
    try {
      const res = await fetch(url, { signal: AbortSignal.timeout(timeoutMs), redirect: 'manual' });
      if (res.status < 500) return { up: true, detail: `HTTP ${res.status}` };
      detail = `HTTP ${res.status}`;
    } catch (e) {
      detail = e instanceof Error ? e.message : String(e);
    }
    if (i < attempts) await sleep(1000 * i);
  }
  return { up: false, detail };
}

export async function checkTenant(tenant: TenantProfile): Promise<PreflightResult> {
  if (usableRoles(tenant).length === 0) {
    return { ok: false, reason: 'no-credentials', detail: `no role of "${tenant.id}" has a usable credential` };
  }
  const p = await probe(tenant.baseUrl);
  return p.up ? { ok: true } : { ok: false, reason: 'env-down', detail: p.detail };
}

/** The reporter reads this file to label the tenant "env-down" rather than a plain failure. */
export function writeDownMarker(tenantId: string, result: Extract<PreflightResult, { ok: false }>): void {
  fs.mkdirSync(REPORT_DIR, { recursive: true });
  fs.writeFileSync(path.join(REPORT_DIR, `environment-down-${tenantId}.json`), JSON.stringify({ tenantId, ...result }, null, 2));
}
