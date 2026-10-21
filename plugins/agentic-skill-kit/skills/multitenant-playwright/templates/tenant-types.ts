import type { Flows } from './flows';

/**
 * One typed profile per tenant. This file is the schema; tenants.example.ts holds the values.
 * Rule: a tenant is DATA. Nothing outside the registry may hard-code a tenant id.
 */

/** Test areas. Every module becomes one Playwright project per tenant. Edit for your app. */
export const MODULES = ['orders', 'billing', 'isolation'] as const;
export type ModuleName = (typeof MODULES)[number];

/** Roles the suite logs in as. Credentials are per tenant AND per role. */
export type Role = 'admin' | 'operator';

/**
 * Capability flags: features that exist for some tenants only.
 * Every key must be written explicitly for every tenant (Record, not Partial):
 * a missing key is a compile error, never a silent "false" fallback.
 */
export type CapabilityFlag = 'otpLogin' | 'bulkImport' | 'approvalStep';
export type Capabilities = Record<CapabilityFlag, boolean>;

/** A REFERENCE to a secret (names of variables), never the secret itself. */
export interface CredentialRef {
  userVar: string;
  passwordVar: string;
}

/** Business values that differ per tenant. Unknown values are todo('why'), see todo.ts. */
export interface TenantData {
  /** Prefix for generated records. Must be unique across tenants (validateRegistry enforces it). */
  recordPrefix: string;
  currency: string;
  contactPhone: string;
}

/** Applicability is data with a reason, so reports can say WHY a cell is n/a. */
export interface Applicability {
  scope: 'in' | 'out';
  reason: string;
}

export interface TenantProfile {
  /** Lowercase slug: letters, digits, hyphens. Used in project names, cache paths, result files. */
  id: string;
  displayName: string;
  /** How the tenant is chosen at login. 'selector' = option in a tenant dropdown; 'subdomain' = host decides. */
  login: { mode: 'selector' | 'subdomain' | 'credentials'; value: string };
  baseUrl: string;
  /** IANA zone. Passed to the browser AND used by helpers; never use the runner clock in steps. */
  timezone: string;
  data: TenantData;
  capabilities: Capabilities;
  /** Per-role credential references. A role that is absent cannot be used on this tenant. */
  credentials: Partial<Record<Role, CredentialRef>>;
  /** Per-module scope with reasons. Missing module = registry validation error. */
  modules: Record<ModuleName, Applicability>;
  /** CI facts live next to the tenant so the pipeline matrix is derived from the registry. */
  ci: { scheduleToken: string; timeoutMinutes: number; credentialsSecret: string };
  /** Behaviour variants: only flows that truly differ. Typed, so a wrong signature fails tsc. */
  overrides?: Partial<Flows>;
}
