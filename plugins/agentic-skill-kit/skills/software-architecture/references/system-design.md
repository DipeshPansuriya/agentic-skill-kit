# System / Solution Design

## Document structure
1. **Context & goal**: problem, users/parties (airline, GHA, forwarder, customs, shipper), success measure
2. **Scope**: in / out
3. **Drivers**: NFR table (below), constraints (regulatory, stack, budget, deadline)
4. **Options & trade-offs**: 2-3 options, weighted table (see SKILL.md)
5. **Recommended design**: C4 L1 context, L2 containers, key sequence, data model sketch
6. **Cross-cutting**: security, observability, deployment, data retention
7. **Risks, open questions, revisit triggers**

## C4 levels: what to draw
| Level | Shows | Audience | Draw when |
|---|---|---|---|
| L1 System Context | The system as one box, users and external systems | Everyone | Always |
| L2 Container | Deployable units: apps, APIs, DBs, brokers, with tech | Architects, devs, ops | Always |
| L3 Component | Major components inside one container | Devs of that container | Complex container only |
| L4 Code | Classes | Rarely | Almost never; generate from code |
Also useful: deployment diagram (regions, AZs, network zones) and dynamic/sequence for key flows.

## NFR table (fill with numbers)
| NFR | Question to answer | Typical target (logistics) | Levers |
|---|---|---|---|
| Scalability | Peak msgs/sec, bookings/day, growth | e.g., 500 msg/s peak FWB/FSU, 3x headroom | Stateless services + horizontal scale, partitioning by tenant/AWB, async queues |
| Availability | Allowed downtime, RPO/RTO | 99.9-99.95%; RPO ≤ 5 min, RTO ≤ 1 h | Multi-AZ, health probes, retries, circuit breakers, active-passive DR |
| Latency | p95/p99 for sync calls; end-to-end for async | API p95 < 300 ms; event-to-status < 60 s | Caching reference data, read models (CQRS), avoid sync chains > 3 hops |
| Throughput / batch | Nightly volumes, bulk uploads | e.g., 1M events/day | Batch + streaming, backpressure, bulk inserts |
| Security | Who can see what; data classification | Tenant isolation; customs data residency | OAuth2/OIDC, per-tenant authz, encryption at rest/in transit, secrets vault |
| Integrability | Partners and message standards | Cargo-IMP, Cargo-XML (IATA), EDIFACT, REST/webhooks | Anti-corruption layer, canonical model, schema versioning |
| Observability | How we detect and trace issues | Trace per AWB/message end-to-end | OpenTelemetry traces, structured logs, SLO dashboards, alerts |
| Cost | Monthly run budget; cost per 1k messages | Stated budget | Serverless/autoscale for spiky loads, reserved capacity for baseline |
| Operability | Who runs it, skill level | Small ops team | Managed services, IaC, runbooks |
| Compliance | Audit, retention | Message audit trail N years | Immutable audit log, retention policies |

## Sizing back-of-envelope
- Peak TPS = daily volume / 86,400 × peak factor (often 5-10 for business hours / flight banks).
- Storage/yr = records/day × avg size × 365 × (1 + index overhead ~0.3-1.0).
- State the formula and inputs; do the arithmetic exactly.

## Production design template

Use this shape for a working system (dashboard BFF, like-counter, live stream, resumable upload), not only C4 boxes.

1. **Authoritative vs derived.** Name the source of truth (e.g. `(post_id, user_id)` relationship). Counts, caches and feeds are derived and may lag. Never treat an evictable cache as the only record of a committed write.
2. **Components table.** Each row: name, purpose, design notes (what it must not do).
3. **Request flows.** Numbered steps for the write path, the undo path, and the read path. State what the client may show immediately vs what is eventually consistent.
4. **Idempotency.** Unique key / conditional write; event id dedupe; state-transition deltas (`absent→present` emits +1, a repeat emits nothing). Outbox or CDC so a committed write cannot lose its event.
5. **Hot keys.** One row that every write hits is a bottleneck. Shard derived counters, hash-bucket partitions, or buffer through a stream. Add shards when load tests show contention, not before.
6. **Client aggregation → BFF.** Many browser calls become one dashboard request; the BFF fans out in parallel, caches with per-part TTLs, returns a purpose-built payload.
7. **Failure modes table.** Timeout + retry, dropped mid-transfer, cache loss, worker lag, abandoned upload. Expected behaviour and how to repair (replay + reconciliation).
8. **Observability.** p50/p95/p99, success vs duplicate vs error, queue lag, drift/reconciliation delta, hot-shard write pressure, cache hit ratio.
9. **Build order.** Correct durable API first; then events; then idempotent consumers; then shards/cache when measured. Do not add distributed parts before the workload needs them.

Multipart / resumable uploads: server initiates and completes; client uploads parts to presigned URLs with parallel limit (3–5), backoff+jitter, ordered ETags on complete, abort on cancel, lifecycle rules for abandoned parts.

## Common logistics building blocks
| Need | Default choice | When to change |
|---|---|---|
| Partner message intake (EDI/IMP/XML) | Gateway → validate → persist raw → queue → parse/translate | Very low volume: synchronous parse is fine |
| Status/event tracking | Append-only event table/stream + projected current-state read model | Few events, simple queries: single table |
| Reference data (airports, carriers, SHCs) | Cached, versioned service or shared read-only DB | — |
| Integration fan-out to many parties | Pub/sub topic with per-subscriber queues | 1-2 consumers: direct queue |
| Documents (eAWB, customs PDFs) | Object storage + metadata DB | — |
