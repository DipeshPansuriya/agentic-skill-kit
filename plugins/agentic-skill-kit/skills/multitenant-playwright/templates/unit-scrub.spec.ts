import * as fs from 'node:fs';
import * as os from 'node:os';
import * as path from 'node:path';
import { expect, test } from '@playwright/test';
import { buildNeedles, scrubDirectory, REDACTED, scrubText } from './scrub-artifacts';
import { headersFromState, isolationHostGuard, tryParseId } from './isolation-helpers';

const b64 = (s: string): string => Buffer.from(s, 'utf8').toString('base64');

function scratch(files: Record<string, string>): string {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'scrub-'));
  for (const [name, body] of Object.entries(files)) fs.writeFileSync(path.join(dir, name), body);
  return dir;
}

test.describe('scrubber', () => {
  test('REGRESSION: overlapping values are replaced longest first (no partial leak)', () => {
    const user = 'admin';
    const pass = 'admin123!';
    const dir = scratch({ 'a.json': JSON.stringify({ u: user, p: pass }) });
    scrubDirectory(dir, [user, pass], [[user, pass]]);
    const out = fs.readFileSync(path.join(dir, 'a.json'), 'utf8');
    expect(out).not.toContain('123!');
    expect(out).not.toContain(pass);
    expect(out).not.toContain(user);
  });

  test('REGRESSION: base64 forms, including a Basic-auth user:password header, are scrubbed', () => {
    const user = 'svc-user';
    const pass = 'p4ss-w0rd';
    const dir = scratch({ 'h.log': `Authorization: Basic ${b64(`${user}:${pass}`)}\nraw=${b64(pass)}\n` });
    scrubDirectory(dir, [user, pass], [[user, pass]]);
    const out = fs.readFileSync(path.join(dir, 'h.log'), 'utf8');
    expect(out).not.toContain(b64(`${user}:${pass}`));
    expect(out).not.toContain(b64(pass));
  });

  test('REGRESSION: a secret shorter than 4 characters fails closed instead of being ignored', () => {
    expect(() => buildNeedles(['abc'])).toThrow(/shorter than 4/);
  });

  test('archives are deleted and reported (fail closed); other text is untouched', () => {
    const dir = scratch({ 'trace.zip': 'PK', 'ok.txt': 'nothing secret here' });
    const r = scrubDirectory(dir, ['longsecret'], []);
    expect(r.deleted).toHaveLength(1);
    expect(fs.existsSync(path.join(dir, 'ok.txt'))).toBe(true);
  });
});


test.describe('scrubber: one level of encoding, file names, symlinks and binaries', () => {
  test('REGRESSION: a URL-encoded value is found in text and in a .har file', () => {
    const pass = 'p4ss-w0rd';
    const dir = scratch({ 'h.log': `u=${encodeURIComponent(pass)}\n`, 'api.har': JSON.stringify({ url: `?q=${encodeURIComponent(pass)}` }) });
    scrubDirectory(dir, [pass], []);
    const log = fs.readFileSync(path.join(dir, 'h.log'), 'utf8');
    expect(log).not.toContain(encodeURIComponent(pass));
    expect(log).toContain(REDACTED);
    expect(fs.readFileSync(path.join(dir, 'api.har'), 'utf8')).not.toContain(encodeURIComponent(pass));
  });

  test('REGRESSION: a value inside unaligned base64 is scrubbed', () => {
    const pass = 'longsecret';
    const dir = scratch({ 'h.log': `blob=X${b64(pass)}\n` });
    scrubDirectory(dir, [pass], []);
    const out = fs.readFileSync(path.join(dir, 'h.log'), 'utf8');
    expect(out).toContain(REDACTED);
    expect(out).not.toContain(b64(pass));
  });

  test('REGRESSION: secret values in file names rename the file with [scrubbed]', () => {
    const pass = 'p4ss-w0rd';
    const dir = scratch({});
    fs.writeFileSync(path.join(dir, `${pass}-report.json`), 'hello');
    scrubDirectory(dir, [pass], []);
    const names = fs.readdirSync(dir);
    expect(names).toContain('[scrubbed]-report.json');
  });

  test('unknown binary types (.webm, images) are deleted even when clean: binaries cannot be proven clean', () => {
    const pass = 'longsecret';
    const dir = scratch({ 'video.webm': `xx${pass}xx`, 'shot.png': '= no secret =' });
    const r = scrubDirectory(dir, [pass], []);
    expect(r.deleted).toHaveLength(2);
    expect(fs.existsSync(path.join(dir, 'video.webm'))).toBe(false);
    expect(fs.existsSync(path.join(dir, 'shot.png'))).toBe(false);
  });

  test('SCRUB_KEEP_BINARY=1 keeps dirty binaries loudly, but they still count as unsafe', () => {
    const pass = 'longsecret';
    const dir = scratch({ 'video.webm': `xx${pass}xx` });
    process.env.SCRUB_KEEP_BINARY = '1';
    try {
      const r = scrubDirectory(dir, [pass], []);
      expect(r.kept).toHaveLength(1);
      expect(r.deleted).toHaveLength(0);
      expect(fs.existsSync(path.join(dir, 'video.webm'))).toBe(true);
      expect(scrubText(`xx${pass}xx`, [pass])).toBe(`xx${REDACTED}xx`);
    } finally {
      delete process.env.SCRUB_KEEP_BINARY;
    }
  });

  test('symlinked artifact paths are refused loudly', () => {
    const dir = scratch({ 'a.json': '{}' });
    let linked = false;
    try {
      fs.symlinkSync(path.join(dir, 'a.json'), path.join(dir, 'link.txt'));
      linked = true;
    } catch {
      /* this host cannot create symlinks */
    }
    if (linked) expect(() => scrubDirectory(dir, ['longsecret'], [])).toThrow(/symlink/);
  });
});

test.describe('isolation host guard (staging-only)', () => {
  test('REGRESSION: refuse without an allowlist, skip with a reason off-list, pass when listed', () => {
    expect(isolationHostGuard(['https://prod.example.com/x'], [])).toMatch(/staging-only and refuse to run/);
    expect(isolationHostGuard(['https://prod.example.com'], ['stg.example.internal'])).toMatch(/not on the TENANT_ISOLATION_ALLOWED_HOSTS/);
    expect(isolationHostGuard(['https://stg.example.internal:8443/a'], ['stg.example.internal:8443'])).toBeUndefined();
  });
});

test.describe('isolation helpers' , () => {
  test('REGRESSION: replay headers are built explicitly from cookies and a bearer token', () => {
    const h = headersFromState({
      cookies: [{ name: 'sid', value: 'abc' }, { name: 'csrf', value: 'xyz' }],
      origins: [{ origin: 'https://x.example.test', localStorage: [{ name: 'accessToken', value: 'tok' }] }],
    });
    expect(h.Cookie).toBe('sid=abc; csrf=xyz');
    expect(h.Authorization).toBe('Bearer tok');
  });

  test('a stored session with no cookies and no token cannot be replayed (the test would be vacuous)', () => {
    expect(() => headersFromState({ cookies: [], origins: [] })).toThrow(/vacuous/);
  });

  test('tryParseId never throws', () => {
    expect(tryParseId('{"id": 7}')).toBe('7');
    expect(tryParseId('<html>oops</html>')).toBeUndefined();
  });
});
