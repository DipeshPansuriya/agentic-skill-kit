import { isTodo } from './todo';

type Plain = Record<string, unknown>;

const isPlain = (v: unknown): v is Plain =>
  typeof v === 'object' && v !== null && !Array.isArray(v) && !isTodo(v);

const BANNED_KEY = /^(?:__proto__|constructor|prototype)$/i;
const ARRAY_INDEX_KEY = /^(?:0|[1-9]\d*)$/;

/**
 * Deep-merge: objects merge, arrays and scalars replace.
 * An overlay key that is not an OWN base key is a typo: throw instead of ignoring it (Object.hasOwn,
 * never "key in": the inherited check accepted prototype keys - the classic pollution vector).
 * Overlay keys that could pollute a prototype (__proto__/constructor/prototype) and array-index keys on
 * plain objects are refused outright: an overlay is data from a file or config, never trusted.
 */
export function deepMerge<T>(base: T, overlay: unknown, path = ''): T {
  if (!isPlain(base) || !isPlain(overlay)) return overlay as T;
  const out: Plain = { ...base };
  for (const [key, value] of Object.entries(overlay)) {
    if (BANNED_KEY.test(key)) throw new Error(`Overlay key "${path}${key}" is refused: prototype-polluting keys are not allowed`);
    if (ARRAY_INDEX_KEY.test(key)) throw new Error(`Overlay array-index key "${path}${key}" is not allowed on a plain object`);
    if (!Object.hasOwn(base as object, key)) throw new Error(`Overlay key "${path}${key}" does not exist on the base profile`);
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
  return profiles.map((p) => (Object.hasOwn(overlay, p.id) ? deepMerge(p, overlay[p.id]) : p));
}
