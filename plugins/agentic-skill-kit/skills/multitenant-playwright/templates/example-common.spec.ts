import { expect, test } from './fixtures';
import { requireRun } from './flows';

/**
 * A COMMON spec: lives in tests/common/orders/ and runs on every tenant that has the "orders" module in scope.
 * Rules shown here:
 *  - the spec calls flows (ctx.flows.*) and never imports steps or tenant files;
 *  - no tenant ternaries: differences come from data (ctx.data), capability flags, or a typed flow override;
 *  - a tenant that lacks a feature skips WITH A REASON taken from data;
 *  - titles are identical on every tenant, so the report matrix lines up in rows.
 * A spec only one tenant has goes in tests/<tenant-id>/orders/ (same fixtures, same rules).
 */
test.describe('orders', () => {
  test('create an order and find it in the list', async ({ ctx }) => {
    await ctx.flows.createOrder(ctx);
    const reference = requireRun<string>(ctx, 'orderReference', 'createOrder');
    await ctx.page.goto('/orders');
    await expect(ctx.page.getByRole('row', { name: new RegExp(reference) })).toBeVisible();
  });

  test('bulk import accepts a valid file', async ({ ctx }) => {
    test.skip(!ctx.tenant.capabilities.bulkImport, 'bulk import is not enabled for this tenant');
    await ctx.page.goto('/orders/import');
    await expect(ctx.page.getByRole('button', { name: 'Upload' })).toBeEnabled(); // Verify: placeholder UI text
  });
});
