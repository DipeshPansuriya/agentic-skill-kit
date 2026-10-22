import { todosByTenant } from './registry';

/**
 * Lists every unfilled todo('why') per tenant, so "what do we still not know about tenant X?" is one command.
 *   npx tsx todos-cli.ts          (exit 0 always: it is a report, not a gate; add --strict to exit 1 when any remain)
 */
let open = 0;
for (const [tenantId, todos] of Object.entries(todosByTenant())) {
  console.log(`${tenantId}: ${todos.length} open`);
  for (const t of todos) console.log(`  - ${t.path}: ${t.why}`);
  open += todos.length;
}
if (process.argv.includes('--strict') && open > 0) process.exit(1);
