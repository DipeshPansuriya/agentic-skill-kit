# Design Patterns: When to Use, When NOT to, Logistics Example

Rule: name the problem first, then the pattern. If a plain function, class or SQL query solves it, use that.

## GoF: Creational
| Pattern | Use when | Do NOT use when | Logistics example |
|---|---|---|---|
| Factory Method / Simple Factory | Type chosen at runtime from data | Only one implementation exists | Create the right parser from message type: `FWB`, `FFM`, `FSU` |
| Abstract Factory | Families of related objects must match | One family only | Per-airline family: message builder + validator + transport |
| Builder | Many optional parts, validated at build | ≤ 4 fields; records/named args suffice | Building a Cargo-XML Waybill with optional OCI, SHC, dims |
| Singleton | One shared, stateless, thread-safe resource | Hides dependencies / mutable state; prefer DI "singleton lifetime" | Reference-data cache registered as DI singleton |
| Prototype | Copying a configured object is cheaper than building | Deep-copy semantics unclear | Clone a booking template for recurring shipments |

## GoF: Structural
| Pattern | Use when | Do NOT use when | Logistics example |
|---|---|---|---|
| Adapter | Wrap a foreign interface to fit yours | You control both sides; just change one | Adapter over a legacy airline SOAP API |
| Facade | Simplify a complex subsystem for callers | It becomes a god-object dumping ground | `CustomsFilingFacade` over validate + sign + submit |
| Decorator | Add cross-cutting behaviour (retry, cache, logging) without changing the class | Framework middleware/pipeline already does it | Caching decorator on `IAirportRepository` |
| Proxy | Control access / lazy load / remote stub | Adds a hop with no control logic | Rate-limiting proxy to a partner API |
| Composite | Tree structures treated uniformly | Flat lists | ULD → pieces → packages weight roll-up |
| Bridge | Two dimensions vary independently | Only one dimension varies | Message format (IMP/XML) × transport (MQ/SFTP/API) |

## GoF: Behavioral
| Pattern | Use when | Do NOT use when | Logistics example |
|---|---|---|---|
| Strategy | Swap algorithms at runtime | 2 branches that never change; an `if` is clearer | Chargeable-weight / rating rules per airline |
| Chain of Responsibility | Ordered, pluggable validation/processing steps | Order is fixed and short | FWB validation: syntax → master data → embargo → DG checks |
| Observer / Pub-Sub (in-process) | Many listeners react to one change | Cross-service events (use a broker) | UI updates when shipment status changes |
| State | Behaviour depends on lifecycle state with many transitions | 2-3 states; an enum + table is enough | AWB lifecycle (see workflow-design skill) |
| Command | Queue, log, undo or retry requests as objects | Simple direct calls | Queued "Send FFM" commands with retry |
| Template Method | Fixed algorithm skeleton, varying steps | Composition (Strategy) is simpler | Base inbound-message pipeline: receive → validate → map → persist |
| Mediator | Many objects talk to each other chaotically | Few collaborators | In-process request handlers (e.g., MediatR-style) for booking commands |
| Specification | Reusable, combinable business rules | One-off predicate | "Eligible for pre-clearance" = DG-free AND value < X AND known shipper |

## Enterprise, Integration and Cloud Patterns
| Pattern | Use when | Do NOT use when | Cost it adds | Logistics example |
|---|---|---|---|---|
| **CQRS** | Read and write loads/shapes differ a lot; many query views | Simple CRUD; one team; reads ≈ writes | Two models, eventual consistency, sync code | Write: bookings; Read: denormalized tracking view for 10k forwarder users |
| **Event Sourcing** | Full audit/history is a core requirement; temporal queries; rebuildable projections | CRUD domain; team new to it; need simple ad-hoc SQL on current state | Versioned events, snapshots, projection rebuilds, GDPR erasure complexity | AWB event history (FSU stream) where current status = fold of events |
| **Saga** (orchestrated or choreographed) | Business transaction spans services with no distributed tx | One DB can hold it: use a local transaction | Compensation logic, state tracking, harder debugging | Booking → capacity hold → payment → confirmation; compensate by releasing capacity |
| **Transactional Outbox** | Must update DB and publish an event reliably | No events; or broker and DB share a transaction | Outbox table + relay (polling or CDC), at-least-once delivery | Insert booking + `BookingCreated` row in one tx; relay publishes |
| **Idempotent Consumer** | Any at-least-once consumer (i.e., nearly all) | Handler is naturally idempotent (pure upsert by key) | Dedupe store with TTL, key design | Store processed `messageId`/AWB+event+timestamp; skip duplicates of FSU |
| **Retry + exponential backoff + jitter** | Transient faults (timeouts, 429, 503) | Non-transient errors (400, validation); non-idempotent calls without idempotency keys | Latency, retry storms if uncapped | Retry partner API 3x: 200 ms, 400 ms, 800 ms ± jitter; then DLQ |
| **Circuit Breaker** | Remote dependency can fail/slow and callers should fail fast | In-process calls; single background job with a retry queue already | Tuning thresholds, fallback design | Open breaker on customs gateway after 50% failures in 30 s; queue filings |
| **Strangler Fig** | Replacing a legacy system incrementally | Small system: rewrite is cheaper; no routing seam exists | Dual running, routing layer, data sync | Route new booking API to new service; legacy keeps old flows until retired |
| **API Gateway** | Many clients/partners need one entry: auth, rate limit, routing | Single internal service; adds latency and a SPOF if self-run | Extra hop, config ownership | Partner gateway for forwarders: OAuth2, per-partner quotas, versioning |
| **Backend for Frontend (BFF)** | Different clients (web, mobile, partner) need different shapes | One client; a generic API fits | One more service per client type | Mobile warehouse app BFF aggregating ULD + task data |
| **Anti-Corruption Layer** | Integrating a legacy/foreign model without polluting yours | Models already match | Mapping code to maintain | Translate Cargo-IMP FFM into the internal manifest model |
| **Competing Consumers** | Scale message processing horizontally | Strict global ordering required | Ordering only per partition/session key | Partition FSU stream by AWB so per-AWB order holds |
| **Bulkhead** | Isolate a noisy dependency/tenant | Low load, single dependency | Pools/queues to size | Separate worker pool for a large airline's feed |
| **Cache-Aside** | Read-heavy, tolerates staleness | Strongly consistent data; low hit rate | Invalidation, stampedes | Airport/carrier reference data, 1 h TTL |
| **Claim Check** | Large payloads through a broker | Small messages | Blob storage + cleanup | Store scanned customs docs in blob; pass URL in event |

## Combinations that work
- Outbox + Idempotent Consumer = effectively-once processing on at-least-once infrastructure.
- Retry (inner) + Circuit Breaker (outer) + Timeout (innermost); never retry inside a retry.
- Strangler Fig + Anti-Corruption Layer for legacy CCS modernisation.
