import * as fs from 'node:fs';
import * as path from 'node:path';

/**
 * Lint-as-architecture for shared steps. Run in the PR pipeline:  npx tsx lint-architecture.ts steps
 *
 * HARD rules (any hit fails):
 *   - shared steps never import tenant data/profiles (tenant knowledge enters through ctx only)
 *   - no runner clock (new Date / Date.now): use the tenant clock helper
 *   - no business literals typed into fields
 * RATCHET rules (count may only fall): the count of sleeps may never exceed the committed baseline.
 * Exempt a reviewed line with a trailing  // allow: <reason>
 */
const HARD: Array<{ rule: string; re: RegExp }> = [
  { rule: 'tenant-import', re: /from\s+['"][^'"]*(tenants?|profiles?|registry)[^'"]*['"]/ },
  { rule: 'runner-clock', re: /\bnew Date\(|\bDate\.now\(/ },
  { rule: 'business-literal', re: /\.(fill|type|pressSequentially)\(\s*['"`][^'"`]{3,}['"`]/ },
];
const RATCHET: Array<{ rule: string; re: RegExp }> = [{ rule: 'sleep', re: /\bwaitForTimeout\s*\(/ }];

const dir = process.argv[2] ?? 'steps';
const baselineFile = process.argv[3] ?? 'lint-baseline.json';
const baseline: Record<string, number> = fs.existsSync(baselineFile) ? (JSON.parse(fs.readFileSync(baselineFile, 'utf8')) as Record<string, number>) : {};

function* files(d: string): Generator<string> {
  for (const e of fs.readdirSync(d, { withFileTypes: true })) {
    const p = path.join(d, e.name);
    if (e.isDirectory()) yield* files(p);
    else if (/\.ts$/.test(e.name)) yield p;
  }
}

const counts: Record<string, number> = {};
const errors: string[] = [];
for (const f of files(dir)) {
  fs.readFileSync(f, 'utf8').split('\n').forEach((line, i) => {
    if (/\/\/\s*allow:/.test(line)) return;
    for (const r of HARD) if (r.re.test(line)) errors.push(`${f}:${i + 1} ${r.rule}`);
    for (const r of RATCHET) if (r.re.test(line)) counts[r.rule] = (counts[r.rule] ?? 0) + 1;
  });
}
for (const r of RATCHET) {
  const now = counts[r.rule] ?? 0;
  const allowed = baseline[r.rule] ?? 0;
  if (now > allowed) errors.push(`ratchet ${r.rule}: ${now} > baseline ${allowed} (the baseline may only fall)`);
  if (now < allowed) console.log(`ratchet ${r.rule}: ${now} < baseline ${allowed}; lower the baseline in ${baselineFile}`);
}
if (errors.length) {
  console.error(errors.join('\n'));
  process.exit(1);
}
console.log('architecture lint passed');
