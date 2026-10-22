import { expect, type Page } from '@playwright/test';
import type { Role, TenantData, TenantProfile } from './tenant-types';
import { requireCredential } from './preflight';

/**
 * Specs call flows through ctx.flows and NEVER import steps directly.
 * A flow is "standard" unless a tenant registers a typed override (tenant.overrides).
 * Overrides are an exceptions list: a tenant that behaves like the baseline has none.
 */

export type RunState = Record<string, unknown>;

export interface TenantContext {
  page: Page;
  tenant: TenantProfile;
  data: TenantData;
  /** Per-test state (fresh object per test, never module-level). Read it with requireRun(). */
  run: RunState;
  flows: Flows;
  /** Unique, tenant-prefixed value; unique across all tests of a worker and across workers; a duplicate throws. */
  unique(kind: string): string;
}

export interface Flows {
  login(ctx: TenantContext, role: Role): Promise<void>;
  createOrder(ctx: TenantContext): Promise<void>;
  updateContact(ctx: TenantContext): Promise<void>;
}

/** A named failure instead of "undefined is not a string" three steps later. */
export function requireRun<T>(ctx: TenantContext, key: string, producedBy: string): T {
  const value = ctx.run[key];
  if (value === undefined) throw new Error(`run.${key} is missing: run "${producedBy}" first (tenant ${ctx.tenant.id})`);
  return value as T;
}

// Locators below are placeholders built from assumed UI text: Verify against the real app.
export const standardFlows: Flows = {
  async login(ctx, role) {
    const cred = requireCredential(ctx.tenant, role);
    const { page, tenant } = ctx;
    await page.goto('/login');
    // The tenant is chosen by data (login.mode), not by a branch on the tenant id.
    if (tenant.login.mode === 'selector') {
      await page.getByLabel('Tenant').selectOption(tenant.login.value);
    }
    await page.getByLabel('Username').fill(cred.user);
    await page.getByLabel('Password').fill(cred.password);
    await page.getByRole('button', { name: 'Sign in' }).click();
    await expect(page.getByRole('navigation')).toBeVisible();
  },

  async createOrder(ctx) {
    const reference = ctx.unique('order');
    await ctx.page.goto('/orders/new');
    await ctx.page.getByLabel('Reference').fill(reference);
    await ctx.page.getByLabel('Currency').selectOption(ctx.data.currency);
    await ctx.page.getByRole('button', { name: 'Save' }).click();
    await expect(ctx.page.getByRole('status')).toContainText('Saved');
    ctx.run.orderReference = reference;
  },

  async updateContact(ctx) {
    await ctx.page.goto('/settings/contact');
    await ctx.page.getByLabel('Phone').fill(ctx.data.contactPhone); // a todo() value throws here, naming tenant and path
    await ctx.page.getByRole('button', { name: 'Save' }).click();
    await expect(ctx.page.getByRole('status')).toContainText('Saved');
  },
};

/**
 * A behaviour variant: only the flow that differs. Keep standard flow untouched (never edit it to make one tenant pass).
 * Register with:  overrides: { createOrder: createOrderWithApproval }   (typed Partial<Flows>)
 */
export const createOrderWithApproval: Flows['createOrder'] = async (ctx) => {
  await standardFlows.createOrder(ctx);
  await ctx.page.getByRole('button', { name: 'Request approval' }).click();
  await expect(ctx.page.getByRole('status')).toContainText('Awaiting approval');
};
