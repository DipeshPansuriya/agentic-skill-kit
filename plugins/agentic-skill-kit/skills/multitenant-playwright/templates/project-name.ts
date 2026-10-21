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
