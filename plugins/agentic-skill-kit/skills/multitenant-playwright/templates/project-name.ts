/**
 * Project names carry tenant and module: "<tenant>__<module>".
 * Tenant ids are slugs (no underscore), so the first "__" is an unambiguous separator.
 * The config builds names with projectName(); the reporter reads them back with parseProjectName().
 * A new tenant therefore needs no reporter change.
 */
export const SEP = '__';
export const SETUP_MODULE = 'setup';

export const projectName = (tenantId: string, module: string): string => `${tenantId}${SEP}${module}`;

export function parseProjectName(name: string): { tenantId: string; module: string } | undefined {
  const i = name.indexOf(SEP);
  if (i <= 0 || i + SEP.length >= name.length) return undefined;
  return { tenantId: name.slice(0, i), module: name.slice(i + SEP.length) };
}

export const SAFE_SLUG = /^[a-z0-9]+(-[a-z0-9]+)*$/;

/**
 * Env-provided tenant, tenant-module and flag lists cross process boundaries and land in file paths and
 * child-process env: every entry must be a safe slug. Empty entries are dropped; anything else throws.
 */
export function safeSlugList(what: string, value: string): string[] {
  const entries = value.split(',').map((s) => s.trim()).filter(Boolean);
  const bad = entries.filter((e) => !SAFE_SLUG.test(e));
  if (bad.length > 0) throw new Error(`${what} entries must be safe slugs (${SAFE_SLUG.source}); bad: ${bad.join(', ')}`);
  return entries;
}
