import * as fs from 'node:fs';
import * as path from 'node:path';
import { registryCredentialPairs } from './scrub-values';

/**
 * Scrub secret VALUES from artifacts before they are published. Fail closed:
 *  - every secret value is replaced, longest first (so "admin" never cuts "admin123!" in half);
 *  - plain-text forms covered: plain, JSON-escaped, HTML-escaped, URL-encoded, base64, and base64 of
 *    "user:pass" (Basic auth header);
 *  - hidden forms covered: ONE level of URL-encoding, or base64 at ANY alignment, found in text AND binary
 *    scans by decoding candidate runs and redacting/deleting when the decoded bytes contain a needle;
 *  - RESIDUAL LIMITS (verify against your artifacts): two or more NESTED encoding levels are not decoded;
 *    partially-encoded or mixed forms (half plain, half percent-encoded) are not matched;
 *    base64 runs whose internal "=" stops the decoder mid-run are not fully scanned;
 *  - a secret shorter than 4 characters cannot be scrubbed without destroying the artifact, so the run FAILS;
 *  - text files (.json/.har/.jsonl/.log/... every trace-like text form) are rewritten in place, after a
 *    binary-style scan too (one decode level, see below);
 *  - ALL other files (.zip, .trace, .webm, images, and any unknown type) are DELETED by default: a binary that
 *    escapes the text scan is not proven clean, and compressed artifacts (traces, archives) cannot be scanned
 *    at all, so tracing is off in CI; add a zip/har rewriter to keep them (verify). Set SCRUB_KEEP_BINARY=1
 *    to keep unsafely-deletable binaries for private debugging instead: they stay UNSCRUBBED and still make
 *    the step FAIL (exit non-zero) unless you publish them by hand;
 *  - images cannot be scanned for typed text: do not run traced tests with real secrets in visible fields;
 *  - secret values that appear in FILE NAMES rename the file into [scrubbed];
 *  - symlinked artifact paths are refused loudly (a symlink can escape the artifact directory);
 *  - the exit code is non-zero if anything was deleted or kept dirty, or the secret set was empty or unusable.
 * The pipeline publishes artifacts only when this step succeeded.
 *   npx tsx scrub-artifacts.ts reports
 */
const TEXT = new Set(['.json', '.har', '.jsonl', '.txt', '.log', '.html', '.htm', '.xml', '.md', '.yml', '.yaml', '.csv']);
const MIN_LENGTH = 4;
export const REDACTED = '[scrubbed]';

const b64 = (s: string): string => Buffer.from(s, 'utf8').toString('base64');

function variants(value: string): string[] {
  const html = value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  const json = JSON.stringify(value).slice(1, -1);
  return [value, json, html, encodeURIComponent(value), b64(value)];
}

/** All search strings for the secrets and user:pass pairs, de-duplicated, longest first. */
export function buildNeedles(secrets: readonly string[], pairs: ReadonlyArray<readonly [string, string]> = []): string[] {
  const short = secrets.filter((s) => s.length < MIN_LENGTH);
  if (short.length > 0) throw new Error(`${short.length} secret value(s) shorter than ${MIN_LENGTH} characters cannot be scrubbed safely: change those test users`);
  const all = [
    ...secrets.flatMap(variants),
    ...pairs.flatMap(([u, p]) => [`${u}:${p}`, b64(`${u}:${p}`)]),
  ];
  return [...new Set(all)].sort((a, b) => b.length - a.length);
}

const containsNeedle = (s: string, needles: readonly string[]): boolean => needles.some((n) => s.includes(n));

/** Decode one level of URL-encoding; sequences that are not valid UTF-8 fall back to a byte-wise latin1 form. */
function percentDecoded(run: string): string {
  try {
    return decodeURIComponent(run);
  } catch {
    return run.replace(/%[0-9A-Fa-f]{2}/g, (h) => String.fromCharCode(parseInt(h.slice(1), 16)));
  }
}

/** Decodable base64 windows of one run: every alignment, so an embedded value at any offset is found. */
function base64DecodedForms(run: string): string[] {
  const out: string[] = [];
  for (let shift = 0; shift < 4; shift++) {
    const w = shift === 0 ? run : run.slice(shift);
    if (w.length < 8) continue;
    const pad = (4 - (w.length % 4)) % 4;
    try {
      out.push(Buffer.from(w + '='.repeat(pad), 'base64').toString('utf8'));
    } catch {
      /* undecodable window: skip */
    }
  }
  return out;
}

/**
 * Scrub a text value: plain replacements first (longest first), then one level of URL-encoding and one level
 * of base64 (any alignment). Exported for unit tests; binary files use the same detection and are NOT rewritten.
 */
export function scrubText(text: string, needles: readonly string[]): string {
  let next = text;
  for (const n of needles) next = next.split(n).join(REDACTED);
  next = next.replace(/(?:%[0-9A-Fa-f]{2}){2,}/g, (run) => (containsNeedle(percentDecoded(run), needles) ? REDACTED : run));
  next = next.replace(/[A-Za-z0-9+/]{12,}={0,2}/g, (run) => (base64DecodedForms(run).some((d) => containsNeedle(d, needles)) ? REDACTED : run));
  return next;
}

const looksDirty = (text: string, needles: readonly string[]): boolean => scrubText(text, needles) !== text;

function* walk(dir: string): Generator<string> {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    if (e.isSymbolicLink()) throw new Error(`refusing symlinked artifact path: ${path.join(dir, e.name)}`);
    const p = path.join(dir, e.name);
    if (e.isDirectory()) yield* walk(p);
    else yield p;
  }
}

export function scrubDirectory(
  dir: string,
  secrets: readonly string[],
  pairs: ReadonlyArray<readonly [string, string]> = [],
): { rewritten: string[]; deleted: string[]; kept: string[] } {
  const needles = buildNeedles(secrets, pairs);
  const rewritten: string[] = [];
  const deleted: string[] = [];
  const kept: string[] = [];
  if (needles.length === 0) return { rewritten, deleted, kept };
  const keepBinary = process.env.SCRUB_KEEP_BINARY === '1';
  for (const file of walk(dir)) {
    const name = path.basename(file);
    const safeName = scrubText(name, needles);
    let target = file;
    if (safeName !== name) {
      target = path.join(path.dirname(file), safeName);
      if (fs.existsSync(target)) throw new Error(`cannot scrub the secret in the file name of "${file}": "${target}" already exists`);
      fs.renameSync(file, target);
      rewritten.push(target);
    }
    const ext = path.extname(target).toLowerCase();
    if (TEXT.has(ext)) {
      const text = fs.readFileSync(target, 'utf8');
      const next = scrubText(text, needles);
      if (next !== text) {
        fs.writeFileSync(target, next);
        rewritten.push(target);
      }
    } else {
      // Fail closed: a binary that escapes the scan is not PROVEN clean (typed text, compressed blocks,
      // unknown encodings), so non-text files are deleted by default; SCRUB_KEEP_BINARY=1 keeps them loudly.
      const dirty = looksDirty(fs.readFileSync(target).toString('latin1'), needles);
      const why = dirty ? 'it may hold a secret' : 'binaries cannot be proven clean here';
      if (keepBinary) {
        console.error(`SCRUB_KEEP_BINARY=1: "${target}" kept although ${why}`);
        kept.push(target);
      } else {
        fs.rmSync(target);
        deleted.push(target);
      }
    }
  }
  return { rewritten, deleted, kept };
}

if (process.argv[1] && /scrub-artifacts\.[tj]s$/.test(process.argv[1])) {
  const dir = process.argv[2];
  if (!dir || !fs.existsSync(dir) || fs.lstatSync(dir).isSymbolicLink()) {
    console.error('usage: scrub-artifacts.ts <artifact-dir> (a symlinked directory is refused)');
    process.exit(2);
  }
  const pairs = registryCredentialPairs();
  const secrets = [...new Set(pairs.flatMap(([u, p]) => [u, p]))];
  if (secrets.length === 0) {
    console.error('No secret values found: refusing to publish unscrubbed artifacts');
    process.exit(1);
  }
  try {
    const r = scrubDirectory(dir, secrets, pairs);
    console.log(`scrubbed ${r.rewritten.length} file(s), deleted ${r.deleted.length} file(s), kept dirty ${r.kept.length} file(s)`);
    process.exit(r.deleted.length > 0 || r.kept.length > 0 ? 1 : 0);
  } catch (e) {
    console.error(e instanceof Error ? e.message : String(e));
    process.exit(1);
  }
}
