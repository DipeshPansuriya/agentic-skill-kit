import * as fs from 'node:fs';
import * as path from 'node:path';
import { registryCredentialValues } from './scrub-values';

/**
 * Scrub secret VALUES from artifacts before they are published. Fail closed:
 * a file that may contain a value and cannot be rewritten is DELETED, and the run exits non-zero if anything was deleted
 * so a human notices. Text files are rewritten in place (plain, JSON-escaped, HTML-escaped, URL-encoded forms).
 * Archives (zip) cannot be rewritten without an unzip library, so they are deleted by default;
 * to keep traces, add a zip library and rewrite entries instead (verify before relying on it).
 *   npx tsx scrub-artifacts.ts reports
 */
const TEXT = new Set(['.json', '.jsonl', '.txt', '.log', '.html', '.htm', '.xml', '.md', '.yml', '.yaml', '.csv']);

function variants(value: string): string[] {
  const html = value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  const json = JSON.stringify(value).slice(1, -1);
  return [...new Set([value, json, html, encodeURIComponent(value)])].filter((v) => v.length >= 4);
}

function* walk(dir: string): Generator<string> {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) yield* walk(p);
    else yield p;
  }
}

export function scrubDirectory(dir: string, secrets: readonly string[]): { rewritten: string[]; deleted: string[] } {
  const all = secrets.flatMap(variants);
  const rewritten: string[] = [];
  const deleted: string[] = [];
  if (all.length === 0) return { rewritten, deleted };
  for (const file of walk(dir)) {
    const ext = path.extname(file).toLowerCase();
    if (TEXT.has(ext)) {
      const text = fs.readFileSync(file, 'utf8');
      let next = text;
      for (const v of all) next = next.split(v).join('[scrubbed]');
      if (next !== text) {
        fs.writeFileSync(file, next);
        rewritten.push(file);
      }
    } else {
      // Binary or archive: look for the raw bytes; archives are compressed, so delete them to fail closed.
      const buf = fs.readFileSync(file);
      const hit = ext === '.zip' || all.some((v) => buf.includes(v));
      if (hit) {
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
  const secrets = registryCredentialValues();
  if (secrets.length === 0) {
    console.error('No credential values found to scrub: refusing to publish unscrubbed artifacts');
    process.exit(1);
  }
  const r = scrubDirectory(dir, secrets);
  console.log(`scrubbed ${r.rewritten.length} file(s), deleted ${r.deleted.length} file(s)`);
  process.exit(r.deleted.length > 0 ? 1 : 0);
}
