import * as fs from 'node:fs';
import * as os from 'node:os';
import * as path from 'node:path';
import { expect, test } from '@playwright/test';
import { buildNeedles, scrubDirectory } from './scrub-artifacts';
import { headersFromState, tryParseId } from './isolation-helpers';

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

test.describe('isolation helpers', () => {
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
