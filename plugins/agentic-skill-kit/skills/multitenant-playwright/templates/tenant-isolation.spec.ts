import { request, type APIRequestContext } from '@playwright/test';
import { expect, test } from './fixtures';
import { authStatePath } from './cache';
import { headersFromState, isolationHostGuard, readState, tryParseId } from './isolation-helpers';
import { getTenant, selectTenants } from './registry';

/**
 * TENANT ISOLATION: the core risk of a multi-tenant product. Lives in tests/common/isolation/, so it runs
 * once per selected tenant (that tenant is the ATTACKER) against every other selected tenant (the VICTIM).
 *
 * Endpoints, status codes, ids and UI text below are placeholders: Verify them against the real product.
 *
 * Rules these tests encode:
 *  - deny means 403 or 404, never 200, and the body must not leak the victim's marker value;
 *  - destructive calls (PUT/DELETE with the victim's id) run only after the read check proved the id does not
 *    resolve in the attacker tenant; with sequential ids the same number could be the attacker's own record,
 *    so prefer GUID ids and keep a canary record that must survive. NON-PRODUCTION DATA ONLY;
 *  - STAGING-ONLY: a host-allowlist guard skips this spec with a reason unless every involved base host is
 *    on TENANT_ISOLATION_ALLOWED_HOSTS: destructive isolation checks never run against production by default;
 *  - the same key in two tenants is two different records;
 *  - a replayed session is built from explicit Cookie / Authorization headers, with a control request that
 *    proves the headers work on the home host (otherwise the replay assertion would pass vacuously);
 *  - nothing is skipped silently: a missing session FAILS (a skipped isolation test is a false green).
 * Run with two or more tenants selected in one process: Model A, or the dedicated isolation job of Model B
 * (TENANTS=a,b MODULES=isolation). Per-tenant jobs exclude this module (EXCLUDE_MODULES=isolation).
 * Prefer dedicated test users for this module so cleanup cannot disturb other specs.
 */
const ATTACKERS = selectTenants(process.env.TENANTS);
const VICTIMS = ATTACKERS.map((t) => t.id);
/**
 * PRODUCTION GUARD (staging-only): destructive isolation checks must never point at production. The spec
 * refuses (skips with a reason) unless every involved base host is on TENANT_ISOLATION_ALLOWED_HOSTS
 * (comma list of host[:port]). See references/isolation.md.
 */
const ALLOWED_HOSTS = (process.env.TENANT_ISOLATION_ALLOWED_HOSTS ?? '').split(',').map((s) => s.trim()).filter(Boolean);
const HOST_REJECT = isolationHostGuard(
  [...new Set([...ATTACKERS.map((t) => t.baseUrl), ...VICTIMS.map((id) => getTenant(id).baseUrl)])],
  ALLOWED_HOSTS,
);
const DENIED = [403, 404];

async function apiAs(sessionOf: string, hostOf: string = sessionOf): Promise<APIRequestContext> {
  readState(authStatePath(sessionOf, 'operator')); // throws with a clear message when the session is missing
  return request.newContext({ baseURL: getTenant(hostOf).baseUrl, storageState: authStatePath(sessionOf, 'operator') });
}

/** Cleanup must never mask the original failure: swallow and log. Falls back to a search by marker. */
async function cleanup(api: APIRequestContext, id: string | undefined, marker: string): Promise<void> {
  try {
    if (id) {
      await api.delete(`/api/orders/${id}`);
      return;
    }
    const list = await api.get(`/api/orders?reference=${encodeURIComponent(marker)}`);
    const rows = (await list.json()) as Array<{ id?: unknown }>;
    for (const row of rows) if (row.id !== undefined) await api.delete(`/api/orders/${String(row.id)}`);
  } catch (e) {
    console.warn(`isolation cleanup failed (ignored): ${e instanceof Error ? e.message : String(e)}`);
  }
}

for (const victimId of VICTIMS) {
  test.describe(`attacker cannot reach tenant ${victimId}`, () => {
    test('read, list, update and delete are denied and nothing leaks', async ({ ctx }) => {
      const { tenant, page } = ctx;
      test.skip(victimId === tenant.id, 'not a cross-tenant pair');
      test.skip(HOST_REJECT !== undefined, HOST_REJECT ? `isolation production guard: ${HOST_REJECT}` : ''); // the only legitimate skip, with a reason

      const mine = await apiAs(tenant.id);
      const theirs = await apiAs(victimId);
      const marker = ctx.unique('isolation');
      const canary = ctx.unique('canary');
      let victimRecord: string | undefined;
      let canaryRecord: string | undefined;
      try {
        const created = await theirs.post('/api/orders', { data: { reference: marker } });
        victimRecord = tryParseId(await created.text()); // tracked before anything else can throw
        expect(created.ok(), 'victim can create its own record').toBeTruthy();
        expect(victimRecord, 'create response carries an id (Verify the response shape)').toBeDefined();

        const own = await mine.post('/api/orders', { data: { reference: canary } });
        canaryRecord = tryParseId(await own.text());
        expect(own.ok(), 'attacker can create its own canary record').toBeTruthy();

        // Precondition for the destructive calls: the victim id must not resolve in the attacker tenant.
        const read = await mine.get(`/api/orders/${victimRecord}`);
        expect(DENIED, `read of ${victimId} record by ${tenant.id}`).toContain(read.status());
        expect(await read.text()).not.toContain(marker);
        expect(victimRecord, 'victim id must differ from the attacker canary id (use GUID ids)').not.toBe(canaryRecord);

        const list = await mine.get('/api/orders');
        expect(await list.text(), 'victim marker must not appear in the attacker list').not.toContain(marker);

        const update = await mine.put(`/api/orders/${victimRecord}`, { data: { reference: 'tampered' } });
        expect(DENIED, 'cross-tenant update').toContain(update.status());
        const remove = await mine.delete(`/api/orders/${victimRecord}`);
        expect(DENIED, 'cross-tenant delete').toContain(remove.status());

        const after = await theirs.get(`/api/orders/${victimRecord}`);
        expect(await after.json(), 'victim record is unchanged').toMatchObject({ reference: marker });
        const canaryAfter = await mine.get(`/api/orders/${canaryRecord}`);
        expect(canaryAfter.ok(), 'attacker canary record survived the destructive calls').toBeTruthy();

        // Same attack through the UI: wait for a positive denied state, THEN assert the marker is absent.
        await page.goto(`/orders/${victimRecord}`);
        await expect(page.getByText(/not found|access denied|forbidden/i)).toBeVisible(); // Verify: product wording
        await expect(page.getByText(marker)).toHaveCount(0);
      } finally {
        await cleanup(theirs, victimRecord, marker);
        await cleanup(mine, canaryRecord, canary);
        await Promise.allSettled([mine.dispose(), theirs.dispose()]);
      }
    });

    test('a session replayed on the victim host is rejected (with a working control)', async ({ tenant }) => {
      test.skip(victimId === tenant.id, 'not a cross-tenant pair');
      test.skip(HOST_REJECT !== undefined, HOST_REJECT ? `isolation production guard: ${HOST_REJECT}` : '');
      const headers = headersFromState(readState(authStatePath(tenant.id, 'operator'))); // Verify token key
      const home = await request.newContext({ baseURL: tenant.baseUrl, extraHTTPHeaders: headers });
      const away = await request.newContext({ baseURL: getTenant(victimId).baseUrl, extraHTTPHeaders: headers });
      try {
        const control = await home.get('/api/orders', { maxRedirects: 0 });
        expect(control.status(), 'control: the replay headers are valid on the attacker home host').toBe(200);
        const res = await away.get('/api/orders', { maxRedirects: 0 });
        const denied = [401, 403].includes(res.status()) || (res.status() >= 300 && res.status() < 400);
        expect(denied, `replayed ${tenant.id} session on ${victimId}: got ${res.status()}`).toBeTruthy();
      } finally {
        await Promise.allSettled([home.dispose(), away.dispose()]);
      }
    });

    test('the same natural key in two tenants is two different records', async ({ ctx }) => {
      const { tenant } = ctx;
      test.skip(victimId === tenant.id, 'not a cross-tenant pair');
      test.skip(HOST_REJECT !== undefined, HOST_REJECT ? `isolation production guard: ${HOST_REJECT}` : '');
      const key = ctx.unique('shared-key'); // identical value written to both tenants
      const mine = await apiAs(tenant.id);
      const theirs = await apiAs(victimId);
      let mineId: string | undefined;
      let theirsId: string | undefined;
      try {
        const a = await mine.post('/api/orders', { data: { reference: key, note: 'mine' } });
        mineId = tryParseId(await a.text());
        const b = await theirs.post('/api/orders', { data: { reference: key, note: 'theirs' } });
        theirsId = tryParseId(await b.text());
        expect(a.ok() && b.ok(), 'both tenants accept the same key').toBeTruthy();
        const [la, lb] = await Promise.all([mine.get(`/api/orders?reference=${key}`), theirs.get(`/api/orders?reference=${key}`)]);
        const [ta, tb] = [await la.text(), await lb.text()];
        expect(ta).toContain('mine');
        expect(ta).not.toContain('theirs');
        expect(tb).toContain('theirs');
        expect(tb).not.toContain('mine');
      } finally {
        await cleanup(mine, mineId, key);
        await cleanup(theirs, theirsId, key);
        await Promise.allSettled([mine.dispose(), theirs.dispose()]);
      }
    });
  });
}
