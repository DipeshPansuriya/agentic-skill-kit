import * as fs from 'node:fs';

/**
 * Helpers for the tenant-isolation spec.
 * Why this exists: Playwright's storageState cookies are scoped to their domain, and an API request context
 * never sends localStorage tokens. Loading the attacker's state into a context pointed at the victim host
 * therefore sends NOTHING, and a "replay rejected" assertion would pass vacuously. The replay test builds the
 * Cookie / Authorization headers explicitly from the stored state, and a control request proves they work.
 */
export interface StoredState {
  cookies?: Array<{ name: string; value: string }>;
  origins?: Array<{ origin: string; localStorage?: Array<{ name: string; value: string }> }>;
}

export function readState(file: string): StoredState {
  if (!fs.existsSync(file)) throw new Error(`No stored session at ${file}: its setup project must run in this process`);
  return JSON.parse(fs.readFileSync(file, 'utf8')) as StoredState;
}

/**
 * Build the request headers a replay attacker would send. `tokenKey` is the localStorage item holding a bearer
 * token (Verify the real key for your product). Throws when the state carries neither cookies nor a token:
 * a replay with no credentials proves nothing.
 */
export function headersFromState(state: StoredState, tokenKey = 'accessToken'): Record<string, string> {
  const headers: Record<string, string> = {};
  const cookies = state.cookies ?? [];
  if (cookies.length > 0) headers.Cookie = cookies.map((c) => `${c.name}=${c.value}`).join('; ');
  for (const origin of state.origins ?? []) {
    const token = origin.localStorage?.find((i) => i.name === tokenKey);
    if (token) {
      headers.Authorization = `Bearer ${token.value}`;
      break;
    }
  }
  if (Object.keys(headers).length === 0) {
    throw new Error('stored session carries neither cookies nor a token: a replay test would be vacuous');
  }
  return headers;
}

/** Extract an id from a JSON body without throwing; undefined when the body is not the expected shape. */
export function tryParseId(text: string): string | undefined {
  try {
    const id = (JSON.parse(text) as { id?: unknown }).id;
    return id === undefined || id === null ? undefined : String(id);
  } catch {
    return undefined;
  }
}
