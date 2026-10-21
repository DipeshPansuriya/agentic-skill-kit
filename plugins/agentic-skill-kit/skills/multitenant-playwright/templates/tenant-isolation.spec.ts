import * as fs from 'node:fs';
import { request, type APIRequestContext } from '@playwright/test';
import { expect, test } from './fixtures';
import { authStatePath } from './cache';
import { allTenantIds, getTenant } from './registry';

/**
 * TENANT ISOLATION: the core risk of a multi-tenant product. Lives in tests/common/isolation/, so it runs
 * once per tenant (that tenant is the ATTACKER) against every other tenant (the VICTIM).
 *
 * Endpoints, status codes and UI text below are placeholders: Verify them against the real product.
 * Rules these tests encode:
 *  - deny means 403 or 404, never 200, and the body must not leak the victim's marker value;
 *  - the same id in two tenants is two different records;
 *  - a session from tenant A replayed on tenant B's host is rejected;
 *  - nothing is skipped silently: a missing session FAILS (a skipped isolation test is a false green).
 * Run these with all involved tenants selected in one process (Model A), or in a dedicated isolation job that
 * holds credentials for the pair (Model B). A per-tenant job cannot see the other tenant's session.
 */
async function apiAs(tenantId: string, baseUrlOf: string = tenantId): Promise<APIRequestContext> {
  const state = authStatePath(tenantId, 'operator');
  if (!fs.existsSync(state)) {
    throw new Error(`No stored session for "${tenantId}". Select that tenant too, so its setup project runs in this process.`);
  }
  return request.newContext({ baseURL: getTenant(baseUrlOf).baseUrl, storageState: state });
}

for (const victimId of allTenantIds()) {
  test.describe(`attacker cannot reach tenant ${victimId}`, () => {
    test('read, list, update and delete are denied and nothing leaks', async ({ ctx }) => {
      const { tenant, page } = ctx;
      test.skip(victimId === tenant.id, 'not a cross-tenant pair'); // the only legitimate skip, with a reason

      const mine = await apiAs(tenant.id);
      const theirs = await apiAs(victimId);
      const marker = ctx.unique('isolation');
      let recordId: string | undefined;
      try {
        const created = await theirs.post('/api/orders', { data: { reference: marker } });
        expect(created.ok(), 'victim can create its own record').toBeTruthy();
        recordId = String(((await created.json()) as { id: string }).id);

        const read = await mine.get(`/api/orders/${recordId}`);
        expect([403, 404], `read of ${victimId} record by ${tenant.id}`).toContain(read.status());
        expect(await read.text()).not.toContain(marker);

        const list = await mine.get('/api/orders');
        expect(await list.text(), 'victim marker must not appear in the attacker list').not.toContain(marker);

        const update = await mine.put(`/api/orders/${recordId}`, { data: { reference: 'tampered' } });
        expect([403, 404], 'cross-tenant update').toContain(update.status());
        const remove = await mine.delete(`/api/orders/${recordId}`);
        expect([403, 404], 'cross-tenant delete').toContain(remove.status());

        const after = await theirs.get(`/api/orders/${recordId}`);
        expect(await after.json(), 'victim record is unchanged').toMatchObject({ reference: marker });

        // Same attack through the UI: the attacker's browser opens the victim's record URL.
        await page.goto(`/orders/${recordId}`);
        await expect(page.getByText(marker)).toHaveCount(0);
      } finally {
        if (recordId) await theirs.delete(`/api/orders/${recordId}`); // clean up what this test created
        await Promise.all([mine.dispose(), theirs.dispose()]);
      }
    });

    test('a session from this tenant is rejected on the victim host', async ({ tenant }) => {
      test.skip(victimId === tenant.id, 'not a cross-tenant pair');
      // Attacker's session cookies sent to the victim's base URL (token replay across tenants).
      const replay = await apiAs(tenant.id, victimId);
      try {
        const res = await replay.get('/api/orders', { maxRedirects: 0 });
        const denied = [401, 403].includes(res.status()) || (res.status() >= 300 && res.status() < 400);
        expect(denied, `replayed ${tenant.id} session on ${victimId}: got ${res.status()}`).toBeTruthy();
      } finally {
        await replay.dispose();
      }
    });
  });
}

test('the same natural key in two tenants is two different records', async ({ ctx }) => {
  const { tenant } = ctx;
  const others = allTenantIds().filter((id) => id !== tenant.id);
  test.skip(others.length === 0, 'only one tenant registered');
  const otherId = others[0] as string;
  const key = ctx.unique('shared-key'); // identical value written to both tenants
  const mine = await apiAs(tenant.id);
  const theirs = await apiAs(otherId);
  const ids: Array<[APIRequestContext, string]> = [];
  try {
    for (const [api, label] of [[mine, 'mine'], [theirs, 'theirs']] as const) {
      const res = await api.post('/api/orders', { data: { reference: key, note: label } });
      expect(res.ok()).toBeTruthy();
      ids.push([api, String(((await res.json()) as { id: string }).id)]);
    }
    const [a, b] = await Promise.all([mine.get(`/api/orders?reference=${key}`), theirs.get(`/api/orders?reference=${key}`)]);
    expect(await a.text()).toContain('mine');
    expect(await a.text()).not.toContain('theirs');
    expect(await b.text()).toContain('theirs');
    expect(await b.text()).not.toContain('mine');
  } finally {
    for (const [api, id] of ids) await api.delete(`/api/orders/${id}`);
    await Promise.all([mine.dispose(), theirs.dispose()]);
  }
});
