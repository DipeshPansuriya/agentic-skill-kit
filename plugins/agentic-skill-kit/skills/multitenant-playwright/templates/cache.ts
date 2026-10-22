import * as fs from 'node:fs';
import * as path from 'node:path';

/**
 * Every cache and result file is keyed by tenant. A shared, tenant-less file is a leak waiting to happen.
 * State dirs must be git-ignored (assertStateDirsGitignored() fails the run loudly otherwise) and files
 * holding live sessions are written with mode 0600 (writePrivate). Add STATE_DIR (default .e2e-state) and
 * the report directory to .gitignore.
 */
export const STATE_DIR = process.env.STATE_DIR ?? '.e2e-state';
export const REPORT_DIR = process.env.REPORT_DIR ?? 'reports';

/** Short-lived: sessions expire server-side. Re-login when older than this. */
export const AUTH_TTL_MS = 30 * 60 * 1000;
/**
 * Prerequisite data (a record created once and reused read-only). The TTL must be shorter than the
 * point where the app's data "rolls over" (a business day, a reservation window), or a cached job outlives its data.
 */
export const PREREQ_TTL_MS = 20 * 60 * 60 * 1000;

const SAFE = /^[a-z0-9]+(-[a-z0-9]+)*$/;

/** Tenant ids AND role names land in file paths: both are safe slugs (nothing with ../, drives or dots). */
const safeName = (what: string, value: string): string => {
  if (!SAFE.test(value)) throw new Error(`Refusing unsafe ${what} "${value}" in a file path`);
  return value;
};

export const authStatePath = (tenantId: string, role: string): string =>
  path.join(STATE_DIR, 'auth', safeName('tenant id', tenantId), `${safeName('role name', role)}.json`);

export const resultFile = (dir: string, tenantId: string, runId: string, ext: string): string =>
  path.join(dir, `${safeName('tenant id', tenantId)}-${runId}.${ext}`);

export function isFresh(file: string, ttlMs: number, now: number = Date.now()): boolean {
  try {
    return now - fs.statSync(file).mtimeMs < ttlMs;
  } catch {
    return false;
  }
}

function writePrivate(file: string, contents: string): Promise<void> {
  fs.writeFileSync(file, contents);
  try {
    fs.chmodSync(file, 0o600); // session data is a secret on disk; storageState-style writers cannot set the mode
  } catch {
    /* file systems without chmod: best effort */
  }
  return Promise.resolve();
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
  path.join(STATE_DIR, 'prereq', safeName('tenant id', tenantId), `${key.replace(/[^a-z0-9-]/gi, '_')}.json`);

export function writePrereq<T>(tenantId: string, key: string, value: T): void {
  const file = prereqPath(tenantId, key);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const envelope: PrereqEnvelope<T> = { tenantId, savedAt: Date.now(), value };
  void writePrivate(file, JSON.stringify(envelope));
}

/** Returns undefined when absent or expired; throws when the file belongs to another tenant (leakage guard). */
export function readPrereq<T>(tenantId: string, key: string, ttlMs: number = PREREQ_TTL_MS, now: number = Date.now()): T | undefined {
  const file = prereqPath(tenantId, key);
  if (!fs.existsSync(file)) return undefined;
  const envelope = JSON.parse(fs.readFileSync(file, 'utf8')) as PrereqEnvelope<T>;
  assertRecordMatchesTenant(envelope.tenantId, tenantId, `Prerequisite cache "${key}"`);
  return now - envelope.savedAt < ttlMs ? envelope.value : undefined;
}

/** Reads the .gitignore of one directory, or undefined when there is none. Injectable for tests. */
export type IgnoreRead = (dir: string) => string | undefined;

function ignoreLines(content: string): string[] {
  return content.split(/\r?\n/).map((l) => l.trim()).filter((l) => l !== '' && !l.startsWith('#'));
}

/**
 * Simplified gitignore matching for ONE ignore line against a repo-relative path. Lenient on purpose
 * (negation lines and mid-path "**" are treated as covering): the goal is fail-loud, not exact git
 * semantics (verify exotic patterns manually).
 */
export function matchesIgnoreLine(line: string, relPosixPath: string): boolean {
  let pattern = line.replace(/\\/g, '/');
  if (pattern.startsWith('!')) pattern = pattern.slice(1);
  if (pattern.startsWith('/')) pattern = pattern.slice(1);
  if (pattern.endsWith('/**')) pattern = pattern.slice(0, -3);
  if (pattern.endsWith('/')) pattern = pattern.slice(0, -1);
  if (pattern === '' || pattern.includes('**')) return false;
  const rel = relPosixPath.replace(/\\/g, '/').replace(/\/+$/, '');
  if (pattern.includes('/')) return rel === pattern || rel.startsWith(`${pattern}/`);
  return rel === pattern || rel.startsWith(`${pattern}/`) || rel.split('/').includes(pattern);
}

/**
 * Fails loudly unless `dir` is covered by a .gitignore at or above it: auth state holds live cookies and
 * must never be committed. `read` returns the .gitignore content of a directory (undefined when absent).
 */
export function assertGitignored(dir: string, read: IgnoreRead): void {
  let at = path.resolve(dir);
  for (;;) {
    if (path.dirname(at) === at) break;
    const gitignore = read(at);
    if (gitignore !== undefined) {
      const rel = path.relative(at, path.resolve(dir));
      if (ignoreLines(gitignore).some((line) => matchesIgnoreLine(line, rel))) return;
    }
    at = path.dirname(at);
  }
  throw new Error(
    `Refusing to run: "${dir}" (session state) is not covered by any .gitignore. ` +
    'State files hold live cookies: add STATE_DIR (and the report dir) to .gitignore or point STATE_DIR outside the repo.',
  );
}

const fsIgnoreRead: IgnoreRead = (dir) => {
  const p = path.join(dir, '.gitignore');
  return fs.existsSync(p) ? fs.readFileSync(p, 'utf8') : undefined;
};

/** Startup gate: run once per worker before any session or report file is written. */
export function assertStateDirsGitignored(read: IgnoreRead = fsIgnoreRead): void {
  assertGitignored(STATE_DIR, read);
  assertGitignored(REPORT_DIR, read);
}
