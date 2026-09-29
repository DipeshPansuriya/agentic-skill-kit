# NoSQL: Choosing and Modelling

## When to choose which store
| Need | Choose | Avoid when |
|---|---|---|
| Relational integrity, ad-hoc reporting, multi-row transactions | PostgreSQL / SQL Server (default choice) | Never "avoid"; start here unless a need below is proven |
| Flexible documents read/written as a whole (booking with nested pieces, dims, handling codes) | MongoDB / Cosmos DB (NoSQL API) | Heavy cross-document joins or reports |
| Cache, sessions, rate limits, counters, leaderboards, short-lived locks | Redis (or Valkey) | It is the only copy of data you cannot lose |
| Massive key-value / single-digit-ms lookups at any scale with known access patterns | DynamoDB / Cosmos DB | Access patterns unknown or change often |
| Full-text search, fuzzy match, faceting, log analytics | Elasticsearch / OpenSearch | System of record (it is a secondary index; re-indexable from source) |
| Time-series metrics | TimescaleDB (PG extension), or partitioned PG tables first | |

Rule of thumb: add a second store only to serve a proven access pattern; keep the relational DB as the source of truth and sync via outbox/CDC.

## Model by access pattern
1. List the queries with frequency and latency target (e.g. "get shipment by AWB, 5k/s, p99 < 20 ms").
2. Design keys and documents so each hot query is **one lookup** (one partition, one document or one index range).
3. Duplicate (denormalise) data read together; accept update fan-out for rarely changing fields.
4. Decide what happens on update of duplicated data (async sync, eventual consistency, acceptable staleness).

## MongoDB (7.x)
**Schema**
- Embed when data is read together and bounded (pieces of a shipment, ≤ hundreds). Reference when unbounded or shared (all events of an AWB over years, customers).
- 16 MB document limit; unbounded arrays (event history) are an anti-pattern: use a separate collection or the **bucket pattern** (one doc per AWB per day with an array of ≤ N events).
- Enforce shape with `$jsonSchema` validators; still version documents (`schemaVersion`).
- Multi-document ACID transactions exist (replica set/sharded) but cost latency; design so most writes touch one document.

**Indexing**
- ESR rule for compound indexes: **E**quality fields, then **S**ort fields, then **R**ange fields.
- `explain("executionStats")`: compare `totalDocsExamined` vs `nReturned`; `COLLSCAN` = no index used.
- Partial indexes (`partialFilterExpression`), TTL indexes (`expireAfterSeconds` on a date field; deletion runs ~every 60 s), unique, wildcard for dynamic keys, text/Atlas Search for search.
- Every index costs RAM (working set) and write time.
- Sharding: pick a high-cardinality, evenly distributed key used by most queries (e.g. `{ awbPrefix: 1, awbNo: 1 }` or hashed); monotonic keys (ObjectId, timestamp) create hot shards when ranged.

**Aggregation**
- `$match` and `$sort` early (they can use indexes only at the start of the pipeline); `$project` to shrink documents; `$lookup` is a join: fine occasionally, a smell on hot paths.
- `allowDiskUse` for large sorts/groups (default on in 6.0+); pipeline stage memory limit 100 MB.
```js
db.awb_events.aggregate([
  { $match: { station: "DXB", ts: { $gte: ISODate("2026-09-01") } } },
  { $group: { _id: "$status", n: { $sum: 1 } } },
  { $sort: { n: -1 } }
])
```

## Redis (7.x)
| Pattern | Commands |
|---|---|
| Cache-aside | `GET k` → miss → load DB → `SET k v EX 300` |
| Distributed lock (single instance) | `SET lock:awb:123 <token> NX PX 30000`; release with a Lua script that checks the token. For correctness-critical locks use DB constraints instead |
| Rate limit | `INCR` + `EXPIRE` (fixed window) or sorted set / token bucket in Lua |
| Counters, dedupe | `INCR`, `SADD`, `SET NX` with TTL for idempotency keys |
| Queues / events | Streams (`XADD`, `XREADGROUP`, `XACK`) with consumer groups; Pub/Sub is fire-and-forget |
| Leaderboard / time-ordered | Sorted sets (`ZADD`, `ZRANGE ... BYSCORE`) |

- **Always set TTLs** on cache keys; add jitter to TTLs to avoid stampedes; consider a short lock or "stale-while-revalidate" for hot keys.
- Eviction (`maxmemory-policy`): `allkeys-lru`/`allkeys-lfu` for pure caches; `volatile-*` only evicts keys with TTL; `noeviction` (default) returns errors when full, right for data you must not lose silently.
- Avoid big keys (> ~1 MB) and `KEYS *` in production (blocks); use `SCAN`.
- Persistence: RDB snapshots and/or AOF (`everysec`); still treat Redis as losable unless designed otherwise.
- Key naming: `app:entity:id[:field]`, e.g. `cargo:awb:176-12345675:status`.
- Invalidate on write (delete key after DB commit), or use write-through; accept a short stale window and document it.

## Key-value / wide-column (DynamoDB, Cosmos DB)
- **Partition key** decides scale: high cardinality, even traffic (e.g. `awbNo`), never a low-cardinality value (`status`, `station`, today's date).
- DynamoDB single-table design: `PK = AWB#176-12345675`, `SK = EVENT#2026-09-27T10:00Z` lets one `Query` return an AWB with its ordered events. GSIs for alternate access (e.g. `GSI1PK = FLIGHT#EK203#2026-09-27`). GSIs are eventually consistent.
- Item limit 400 KB (DynamoDB); 2 MB (Cosmos DB). Hot partitions throttle: add write sharding (suffix) when a key is too hot.
- Cosmos DB: choose partition key for both even writes and in-partition queries; cross-partition queries cost more RU. Consistency levels: Strong, Bounded Staleness, **Session** (default), Consistent Prefix, Eventual.
- Use TTL for expiring data; streams/change feed for projections.

## Elasticsearch / OpenSearch basics
- Secondary search index fed from the system of record (CDC/outbox); must be rebuildable.
- Define explicit mappings: `keyword` for IDs/codes (AWB, station), `text` for free text, `date`, numeric types. Dynamic mapping of everything leads to mapping explosion.
- Use `filter` context (cached, no scoring) for exact matches; `query` context for relevance.
- Shard sizing: roughly 10–50 GB per shard; time-based indices with ILM/ISM rollover and retention.
- Deep paging: `search_after` + point-in-time, not large `from`.
- Near-real-time: documents are searchable after refresh (default 1 s).

## Consistency trade-offs
- CAP in practice: during a partition choose consistency or availability; otherwise the trade is **latency vs consistency** (PACELC).
- Read-your-writes: read from primary or use session consistency / causal sessions (Mongo `readConcern: "majority"` + causally consistent sessions).
- Mongo durable writes: `writeConcern: { w: "majority" }`.
- Cross-store updates are not atomic: use the transactional outbox + idempotent consumers; never dual-write from app code without reconciliation.
- State the staleness users will see ("search results may lag up to 2 s") in the design.
