/**
 * "Decide" step of Model B as a PURE function: which tenants run in this pipeline run?
 * It never reads files or the environment, so contract tests can drive it with the real registry.
 * It fails instead of skipping: selecting nothing is an error, never a silent green.
 */
export interface DecideTenant {
  id: string;
  scheduleToken: string;
  timeoutMinutes: number;
  credentialsSecret: string;
}

export interface DecideInput {
  reason: 'schedule' | 'manual';
  /** The schedule's display name; a tenant is selected when its token appears as a whole word. */
  scheduleName?: string;
  /** Manual run: tenant id -> run it? Unknown ids throw (a typo must not silently skip a tenant). */
  manual?: Record<string, boolean>;
  tenants: readonly DecideTenant[];
}

const escape = (s: string): string => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

export function tokenInName(token: string, name: string): boolean {
  // Whole word: "nightly-a" must not match inside "nightly-ab".
  return new RegExp(`(^|[^a-z0-9-])${escape(token)}($|[^a-z0-9-])`, 'i').test(name);
}

export function decide(input: DecideInput): DecideTenant[] {
  let chosen: DecideTenant[];
  if (input.reason === 'schedule') {
    const name = input.scheduleName ?? '';
    chosen = input.tenants.filter((t) => tokenInName(t.scheduleToken, name));
  } else {
    const flags = input.manual ?? {};
    const known = new Set(input.tenants.map((t) => t.id));
    for (const id of Object.keys(flags)) {
      if (!known.has(id)) throw new Error(`decide: manual selection names unknown tenant "${id}"`);
    }
    chosen = input.tenants.filter((t) => flags[t.id] === true);
  }
  if (chosen.length === 0) {
    throw new Error(`decide: no tenant selected for reason "${input.reason}"; refusing to skip silently`);
  }
  return chosen;
}

/** GitHub Actions style: strategy.matrix = fromJSON(...) */
export const toIncludeMatrix = (tenants: readonly DecideTenant[]): string =>
  JSON.stringify({
    include: tenants.map((t) => ({ tenant: t.id, timeout: t.timeoutMinutes, credentialsSecret: t.credentialsSecret })),
  });

/** Azure DevOps style: a map of job-name -> variables (use with a matrix expression). */
export const toKeyedMatrix = (tenants: readonly DecideTenant[]): string =>
  JSON.stringify(
    Object.fromEntries(
      tenants.map((t) => [t.id.replace(/-/g, '_'), { tenant: t.id, timeout: String(t.timeoutMinutes), credentialsSecret: t.credentialsSecret }]),
    ),
  );

/** A CLI-supplied repo-relative path is either usable or refused with a reason (CLI: usage error, exit 2). */
export type SafePath = { ok: true; path: string } | { ok: false; reason: string };

/**
 * Resolve a CLI-supplied repo-relative path against repoRoot. Absolute paths (POSIX /, UNC \, drive C:),
 * parent traversal (".." segments) and empty results are REFUSED, so a config file like --schedule-map can
 * never point outside the repo. Pure string logic; the caller decides the exit code.
 */
export function safeRepoRelativePath(input: string, repoRoot: string): SafePath {
  const trimmed = input.trim().replace(/^['"]|['"]$/g, '');
  if (trimmed === '') return { ok: false, reason: 'empty path' };
  const low = trimmed.toLowerCase();
  if (low.startsWith('/') || low.startsWith('\\\\') || /^[a-z]:/.test(low)) return { ok: false, reason: `absolute path refused: "${trimmed}"` };
  const parts = trimmed.split(/[\\/]/).filter((p) => p !== '' && p !== '.');
  if (parts.length === 0) return { ok: false, reason: `"${trimmed}" resolves to nothing` };
  if (parts.some((p) => p === '..')) return { ok: false, reason: `parent traversal refused: "${trimmed}"` };
  const root = repoRoot.replace(/[\\/]+$/, '');
  const sep = root.includes('\\') ? '\\' : '/';
  return { ok: true, path: [root, ...parts].join(sep) };
}
