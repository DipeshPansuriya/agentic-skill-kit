# Microservices vs Modular Monolith

Default: **start with a modular monolith** (one deployable, strict internal module boundaries, one DB with schema-per-module). Extract a service only when a specific driver below is true and measured.

## Decision table (score the user's context)
| Driver | Favors modular monolith | Favors microservices |
|---|---|---|
| Teams | 1-3 teams; < ~25 engineers | Many autonomous teams blocked on each other's releases |
| Domain clarity | Boundaries still moving | Stable, well-understood bounded contexts |
| Scaling profile | Uniform load | One part has 10x+ different load or scaling pattern (e.g., FSU event ingestion vs admin UI) |
| Release cadence | Shared cadence acceptable | Parts must release independently many times a day |
| Tech heterogeneity | One stack | A part genuinely needs a different runtime |
| Fault isolation | Acceptable to fail together | One part's failure must not stop others (e.g., customs filing vs tracking) |
| Ops maturity | No platform team, limited observability | CI/CD per service, tracing, service mesh/gateway, on-call per team |
| Data consistency | Many cross-module transactions | Few cross-boundary transactions; eventual consistency acceptable |
| Compliance | Single boundary simpler | Isolate regulated data (e.g., customs data residency) |

Rule of thumb: if fewer than 3 "favors microservices" rows are clearly true, stay modular monolith and extract selectively.

## Modular monolith rules (so extraction stays possible)
- Modules talk via public interfaces or in-process events, never each other's tables.
- Schema per module; no cross-module joins in code (use read models).
- Architecture tests enforce boundaries (ArchUnit / NetArchTest).
- Integration events already go through an outbox, so moving to a broker later is a transport change.

## Extraction path
1. Identify the module with the strongest driver (scale, fault isolation, team).
2. Make its boundary clean inside the monolith first (no shared tables).
3. Put the module behind an API/event contract; add an outbox.
4. Deploy it separately; route with Strangler Fig; keep a rollback switch.
5. Move its data; retire the in-monolith code.

## Anti-patterns
| Anti-pattern | Symptom |
|---|---|
| Distributed monolith | Services deploy together, share DB, long sync call chains |
| Nano-services | One service per entity/CRUD; more services than engineers |
| Shared "common" library with domain logic | Every change forces all services to redeploy |
