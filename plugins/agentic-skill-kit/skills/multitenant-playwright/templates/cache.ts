import * as fs from 'node:fs';
import * as path from 'node:path';

/**
 * Every cache and result file is keyed by tenant. A shared, tenant-less file is a leak waiting to happen.
 * Add STATE_DIR (default .e2e-state) and the report directory to .gitignore.
 */
export const STATE_DIR = process.env.STATE_DIR ?? '.e2e-state';
export const REPORT_DIR = process.env.REPORT_DIR ?? 'reports';

/** Short-lived: sessions expire server-side. Re-login when older than this. */
export const AUTH_TTL_MS = 30 * 60 * 1000;
/**
 * Prerequisite data (a record created once and reused read-only). The TTL must be shorter than the
 * point where the app's data "rolls over" (a business day, a booking window), or a cached job outlives its data.
 */
export const PREREQ_TTL_MS = 20 * 60 * 60 * 1000;

const SAFE = /^[a-z0-9]+(-[a-z0-9]+)*$/;
const safeId = (tenantId: string): string => {
  if (!SAFE.test(tenantId)) throw new Error(`Refusing unsafe tenant id "${tenantId}" in a file path`);
  return tenantId;
};

export const authStatePath = (tenantId: string, role: string): string =>
  path.join(STATE_DIR, 'auth', safeId(tenantId), `${role}.json`);

export const resultFile = (dir: string, tenantId: string, runId: string, ext: string): string =>
  path.join(dir, `${safeId(tenantId)}-${runId}.${ext}`);

export function isFresh(file: string, ttlMs: number, now: number = Date.now()): boolean {
  try {
    return now - fs.statSync(file).mtimeMs < ttlMs;
  } catch {
    return false;
  }
}

/** Throws when a recorded tenant differs from the one asking. A mismatched record must never be applied. */
export function assertRecordMatchesTenant(recordedTenantId: string, expectedTenantId: string, what: string): void {
  if (recordedTenantId !== expectedTenantId) {
    throw new Error(`${what} was recorded for tenant "${recordedTenantId}" but this run is tenant "${expectedTenantId}"`);
  }
}

interface PrereqEnvelope<T> {
  tenantId: string;
  savedAt: number;
  value: T;
}

const prereqPath = (tenantId: string, key: string): string =>
  path.join(STATE_DIR, 'prereq', safeId(tenantId), `${key.replace(/[^a-z0-9-]/gi, '_')}.json`);

export function writePrereq<T>(tenantId: string, key: string, value: T): void {
  const file = prereqPath(tenantId, key);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const envelope: PrereqEnvelope<T> = { tenantId, savedAt: Date.now(), value };
  fs.writeFileSync(file, JSON.stringify(envelope));
}

/** Returns undefined when absent or expired; throws when the file belongs to another tenant (leakage guard). */
export function readPrereq<T>(tenantId: string, key: string, ttlMs: number = PREREQ_TTL_MS, now: number = Date.now()): T | undefined {
  const file = prereqPath(tenantId, key);
  if (!fs.existsSync(file)) return undefined;
  const envelope = JSON.parse(fs.readFileSync(file, 'utf8')) as PrereqEnvelope<T>;
  assertRecordMatchesTenant(envelope.tenantId, tenantId, `Prerequisite cache "${key}"`);
  return now - envelope.savedAt < ttlMs ? envelope.value : undefined;
}
