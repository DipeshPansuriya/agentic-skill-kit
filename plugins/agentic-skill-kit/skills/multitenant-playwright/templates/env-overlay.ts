import { isTodo } from './todo';

type Plain = Record<string, unknown>;

const isPlain = (v: unknown): v is Plain =>
  typeof v === 'object' && v !== null && !Array.isArray(v) && !isTodo(v);

/**
 * Deep-merge: objects merge, arrays and scalars replace.
 * An overlay key that does not exist in the base is a typo: throw instead of ignoring it.
 */
export function deepMerge<T>(base: T, overlay: unknown, path = ''): T {
  if (!isPlain(base) || !isPlain(overlay)) return overlay as T;
  const out: Plain = { ...base };
  for (const [key, value] of Object.entries(overlay)) {
    if (!(key in base)) throw new Error(`Overlay key "${path}${key}" does not exist on the base profile`);
    out[key] = deepMerge(base[key], value, `${path}${key}.`);
  }
  return out as T;
}

/** Apply a named environment profile. Unknown profile name or unknown tenant id throws. */
export function applyOverlay<T extends { id: string }>(
  profiles: readonly T[],
  overlays: Record<string, Record<string, unknown>>,
  envName: string | undefined,
): T[] {
  if (!envName) return [...profiles];
  const overlay = overlays[envName];
  if (!overlay) throw new Error(`Unknown environment profile "${envName}". Known: ${Object.keys(overlays).join(', ')}`);
  const ids = new Set(profiles.map((p) => p.id));
  for (const id of Object.keys(overlay)) {
    if (!ids.has(id)) throw new Error(`Environment "${envName}" names unknown tenant "${id}"`);
  }
  return profiles.map((p) => (p.id in overlay ? deepMerge(p, overlay[p.id]) : p));
}
