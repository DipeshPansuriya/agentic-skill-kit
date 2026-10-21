import * as fs from 'node:fs';
import * as path from 'node:path';
import { registryCredentialPairs } from './scrub-values';

/**
 * Scrub secret VALUES from artifacts before they are published. Fail closed:
 *  - every credential value is replaced, longest first (so "admin" never cuts "admin123!" in half);
 *  - forms covered: plain, JSON-escaped, HTML-escaped, URL-encoded, base64, and base64 of "user:password"
 *    (Basic auth header). Base64 covers the aligned form only; an embedded value at another offset is not found (verify);
 *  - a secret shorter than 4 characters cannot be scrubbed without destroying the artifact, so the run FAILS;
 *  - a file that may hold a value and cannot be rewritten is DELETED; every .zip is deleted (traces and report data
 *    are compressed and cannot be rewritten here), so tracing is off in CI; add a zip rewriter to keep them (verify);
 *  - images cannot be scanned for typed text: do not run traced tests with real secrets in visible fields;
 *  - the exit code is non-zero if anything was deleted or the secret set was empty or unusable.
 * The pipeline publishes artifacts only when this step succeeded.
 *   npx tsx scrub-artifacts.ts reports
 */
const TEXT = new Set(['.json', '.jsonl', '.txt', '.log', '.html', '.htm', '.xml', '.md', '.yml', '.yaml', '.csv']);
const MIN_LENGTH = 4;

const b64 = (s: string): string => Buffer.from(s, 'utf8').toString('base64');

function variants(value: string): string[] {
  const html = value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  const json = JSON.stringify(value).slice(1, -1);
  return [value, json, html, encodeURIComponent(value), b64(value)];
}

/** All search strings for the secrets and user:password pairs, de-duplicated, longest first. */
export function buildNeedles(secrets: readonly string[], pairs: ReadonlyArray<readonly [string, string]> = []): string[] {
  const short = secrets.filter((s) => s.length < MIN_LENGTH);
  if (short.length > 0) throw new Error(`${short.length} secret value(s) shorter than ${MIN_LENGTH} characters cannot be scrubbed safely: change the test credentials`);
  const all = [
    ...secrets.flatMap(variants),
    ...pairs.flatMap(([u, p]) => [`${u}:${p}`, b64(`${u}:${p}`)]),
  ];
  return [...new Set(all)].sort((a, b) => b.length - a.length);
}

function* walk(dir: string): Generator<string> {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) yield* walk(p);
    else yield p;
  }
}

export function scrubDirectory(
  dir: string,
  secrets: readonly string[],
  pairs: ReadonlyArray<readonly [string, string]> = [],
): { rewritten: string[]; deleted: string[] } {
  const needles = buildNeedles(secrets, pairs);
  const rewritten: string[] = [];
  const deleted: string[] = [];
  if (needles.length === 0) return { rewritten, deleted };
  for (const file of walk(dir)) {
    const ext = path.extname(file).toLowerCase();
    if (TEXT.has(ext)) {
      const text = fs.readFileSync(file, 'utf8');
      let next = text;
      for (const n of needles) next = next.split(n).join('[scrubbed]'); // longest first
      if (next !== text) {
        fs.writeFileSync(file, next);
        rewritten.push(file);
      }
    } else {
      const buf = fs.readFileSync(file);
      if (ext === '.zip' || needles.some((n) => buf.includes(n))) {
        fs.rmSync(file);
        deleted.push(file);
      }
    }
  }
  return { rewritten, deleted };
}

if (process.argv[1] && /scrub-artifacts\.[tj]s$/.test(process.argv[1])) {
  const dir = process.argv[2];
  if (!dir || !fs.existsSync(dir)) {
    console.error('usage: scrub-artifacts.ts <artifact-dir>');
    process.exit(2);
  }
  const pairs = registryCredentialPairs();
  const secrets = [...new Set(pairs.flatMap(([u, p]) => [u, p]))];
  if (secrets.length === 0) {
    console.error('No credential values found to scrub: refusing to publish unscrubbed artifacts');
    process.exit(1);
  }
  try {
    const r = scrubDirectory(dir, secrets, pairs);
    console.log(`scrubbed ${r.rewritten.length} file(s), deleted ${r.deleted.length} file(s)`);
    process.exit(r.deleted.length > 0 ? 1 : 0);
  } catch (e) {
    console.error(e instanceof Error ? e.message : String(e));
    process.exit(1);
  }
}
