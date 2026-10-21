import * as fs from 'node:fs';
import { expect, test } from '@playwright/test';
import { decide, tokenInName, toIncludeMatrix, type DecideTenant } from './decide';
import { rawTenants } from './registry';

const registryTenants = (): DecideTenant[] =>
  rawTenants().map((t) => ({
    id: t.id,
    scheduleToken: t.ci.scheduleToken,
    timeoutMinutes: t.ci.timeoutMinutes,
    credentialsSecret: t.ci.credentialsSecret,
  }));

test.describe('decide (pure function, driven by the real registry)', () => {
  test('a scheduled run selects the tenant whose token is a whole word', () => {
    const first = registryTenants()[0] as DecideTenant;
    expect(decide({ reason: 'schedule', scheduleName: `Weeknight ${first.scheduleToken} run`, tenants: registryTenants() }).map((t) => t.id)).toEqual([first.id]);
    expect(tokenInName('nightly-a', 'nightly-ab')).toBe(false);
  });

  test('manual selection honours flags and rejects unknown tenants', () => {
    const ids = registryTenants().map((t) => t.id);
    const manual = Object.fromEntries(ids.map((id, i) => [id, i === 0]));
    expect(decide({ reason: 'manual', manual, tenants: registryTenants() }).map((t) => t.id)).toEqual([ids[0]]);
    expect(() => decide({ reason: 'manual', manual: { nope: true }, tenants: registryTenants() })).toThrow(/unknown tenant/);
  });

  test('selecting nothing is an error, never a silent skip', () => {
    expect(() => decide({ reason: 'schedule', scheduleName: 'no token here', tenants: registryTenants() })).toThrow(/refusing to skip/);
    expect(() => decide({ reason: 'manual', manual: {}, tenants: registryTenants() })).toThrow(/refusing to skip/);
  });

  test('matrix output carries only reference names, never secret values', () => {
    const json = toIncludeMatrix(registryTenants());
    for (const t of registryTenants()) expect(json).toContain(t.credentialsSecret);
  });
});

/**
 * CONTRACT: the pipeline file and the registry cannot drift.
 * The pipeline must derive its tenants from decide(); a tenant id written into the YAML is a hand-written list.
 */
test.describe('pipeline contract', () => {
  const file = process.env.PIPELINE_FILE ?? 'ci/pipeline.yml';

  test('pipeline file exists', () => {
    expect(fs.existsSync(file), `set PIPELINE_FILE (looked for ${file})`).toBeTruthy();
  });

  test('no tenant id is hand-written in the pipeline', () => {
    const yaml = fs.readFileSync(file, 'utf8');
    for (const t of rawTenants()) expect(yaml, `pipeline names tenant "${t.id}"`).not.toContain(t.id);
  });

  test('every cron in the pipeline is mapped to a name, and every mapped name selects a tenant', () => {
    const yaml = fs.readFileSync(file, 'utf8');
    const map = JSON.parse(fs.readFileSync(process.env.SCHEDULE_MAP ?? 'ci/schedules.json', 'utf8')) as Record<string, string>;
    const crons = [...yaml.matchAll(/cron:\s*'([^']+)'/g)].map((m) => m[1] as string);
    expect(crons.length, 'pipeline has at least one schedule').toBeGreaterThan(0);
    for (const cron of crons) expect(map[cron], `cron "${cron}" missing from the schedule map`).toBeTruthy();
    for (const [cron, name] of Object.entries(map)) {
      expect(() => decide({ reason: 'schedule', scheduleName: name, tenants: registryTenants() }), `schedule "${cron}"`).not.toThrow();
    }
  });

  test('no literal secret assignment in the pipeline', () => {
    const yaml = fs.readFileSync(file, 'utf8');
    const literal = /^\s*[A-Za-z0-9_]*(PASSWORD|SECRET|TOKEN|KEY)[A-Za-z0-9_]*\s*:\s*(?!\$\{\{|\$\(|['"]?\$)\S+/im;
    expect(yaml).not.toMatch(literal);
  });
});
