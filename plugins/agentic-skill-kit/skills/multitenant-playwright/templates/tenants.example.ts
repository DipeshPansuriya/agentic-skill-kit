import type { TenantProfile } from './tenant-types';
import { createOrderWithApproval } from './flows';
import { todo } from './todo';

/**
 * Example profiles. Replace with your tenants; keep ids generic in shared docs.
 * Adding a tenant = add one object here. Projects, CI matrix and report columns follow.
 */
export const tenantA: TenantProfile = {
  id: 'tenant-a',
  displayName: 'Tenant A',
  login: { mode: 'selector', value: 'tenant-a' },
  baseUrl: 'https://tenant-a.example.test',
  timezone: 'Europe/London',
  data: { recordPrefix: 'TA', currency: 'GBP', contactPhone: '+44 20 7946 0000' },
  capabilities: { otpLogin: false, bulkImport: true, approvalStep: false },
  credentials: {
    admin: { userVar: 'E2E_TENANT_A_ADMIN_USER', passwordVar: 'E2E_TENANT_A_ADMIN_PASSWORD' },
    operator: { userVar: 'E2E_TENANT_A_OPERATOR_USER', passwordVar: 'E2E_TENANT_A_OPERATOR_PASSWORD' },
  },
  modules: {
    orders: { scope: 'in', reason: 'core flow' },
    billing: { scope: 'in', reason: 'core flow' },
    isolation: { scope: 'in', reason: 'tenant isolation is always in scope' },
  },
  ci: { scheduleToken: 'nightly-a', timeoutMinutes: 90, credentialsSecret: 'E2E_TENANT_A_CREDENTIALS' },
};

export const tenantB: TenantProfile = {
  id: 'tenant-b',
  displayName: 'Tenant B',
  login: { mode: 'selector', value: 'tenant-b' },
  baseUrl: 'https://tenant-b.example.test',
  timezone: 'Asia/Dubai',
  // Not yet verified on this tenant: reading it fails loudly, naming tenant and path.
  data: { recordPrefix: 'TB', currency: 'AED', contactPhone: todo('ask the tenant admin for a valid test number') },
  // Unknown reads as dangerous: if you do not know, write the value that makes tests fail or skip loudly.
  capabilities: { otpLogin: true, bulkImport: false, approvalStep: true },
  credentials: {
    operator: { userVar: 'E2E_TENANT_B_OPERATOR_USER', passwordVar: 'E2E_TENANT_B_OPERATOR_PASSWORD' },
  },
  modules: {
    orders: { scope: 'in', reason: 'core flow' },
    billing: { scope: 'out', reason: 'billing is not licensed for this tenant' },
    isolation: { scope: 'in', reason: 'tenant isolation is always in scope' },
  },
  ci: { scheduleToken: 'nightly-b', timeoutMinutes: 60, credentialsSecret: 'E2E_TENANT_B_CREDENTIALS' },
  // Only this tenant approves orders: one typed override, the standard flow stays untouched.
  overrides: { createOrder: createOrderWithApproval },
};

/** Named environment overlays (deep-merged over the profile). Unknown env or unknown key = error. */
export const overlays: Record<string, Record<string, unknown>> = {
  staging: {
    'tenant-a': { baseUrl: 'https://tenant-a.staging.example.test' },
    'tenant-b': { baseUrl: 'https://tenant-b.staging.example.test' },
  },
};
