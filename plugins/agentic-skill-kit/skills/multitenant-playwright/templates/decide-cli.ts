import * as fs from 'node:fs';
import { decide, toIncludeMatrix, toKeyedMatrix, type DecideInput } from './decide';
import { rawTenants } from './registry';

/**
 * Thin CLI over decide(). Tenants come from the registry, never from the pipeline file.
 *   npx tsx decide-cli.ts --reason schedule --schedule "nightly-a" --format github
 *   npx tsx decide-cli.ts --reason schedule --cron "0 20 * * 0-4" --schedule-map ci/schedules.json
 *   npx tsx decide-cli.ts --reason manual --manual tenant-a,tenant-b            (a bare id means true)
 *   npx tsx decide-cli.ts --reason manual --manual tenant-a=true,tenant-b=false --format azure
 *   npx tsx decide-cli.ts --reason manual --all
 * (tsx is one way to run TypeScript; ts-node or a compiled build work equally.)
 */
function arg(name: string): string | undefined {
  const i = process.argv.indexOf(`--${name}`);
  return i >= 0 ? process.argv[i + 1] : undefined;
}

try {
  const reason = arg('reason');
  if (reason !== 'schedule' && reason !== 'manual') throw new Error('--reason must be "schedule" or "manual"');
  const manual: Record<string, boolean> = {};
  for (const pair of (arg('manual') ?? '').split(',').map((p) => p.trim()).filter(Boolean)) {
    const [id, value = 'true'] = pair.split('=');
    if (!id || (value !== 'true' && value !== 'false')) throw new Error(`bad --manual entry "${pair}"`);
    manual[id] = value === 'true';
  }
  if (process.argv.includes('--all')) for (const t of rawTenants()) manual[t.id] = true;
  let scheduleName = arg('schedule') ?? '';
  const cron = arg('cron');
  if (cron !== undefined) {
    // GitHub-style schedules give the cron string, not a name: map it with a small data file.
    const mapFile = arg('schedule-map');
    if (!mapFile) throw new Error('--cron needs --schedule-map <file.json>');
    const map = JSON.parse(fs.readFileSync(mapFile, 'utf8')) as Record<string, string>;
    const name = map[cron];
    if (!name) throw new Error(`cron "${cron}" is not in ${mapFile}: add it, or scheduled runs would select nothing`);
    scheduleName = name;
  }
  const input: DecideInput = {
    reason,
    scheduleName,
    manual,
    tenants: rawTenants().map((t) => ({
      id: t.id,
      scheduleToken: t.ci.scheduleToken,
      timeoutMinutes: t.ci.timeoutMinutes,
      credentialsSecret: t.ci.credentialsSecret,
    })),
  };
  const chosen = decide(input);
  const ids = chosen.map((t) => t.id).join(',');
  if (arg('format') === 'azure') {
    // Azure DevOps: set an output variable consumed by the tenant jobs.
    console.log(`##vso[task.setvariable variable=matrix;isOutput=true]${toKeyedMatrix(chosen)}`);
    console.log(`##vso[task.setvariable variable=tenants;isOutput=true]${ids}`);
  } else {
    // "tenants" is the EXPECTED list the combine step checks results against.
    const lines = `matrix=${toIncludeMatrix(chosen)}\ntenants=${ids}\n`;
    if (process.env.GITHUB_OUTPUT) fs.appendFileSync(process.env.GITHUB_OUTPUT, lines);
    else console.log(lines);
  }
} catch (e) {
  console.error(e instanceof Error ? e.message : String(e));
  process.exit(1);
}
