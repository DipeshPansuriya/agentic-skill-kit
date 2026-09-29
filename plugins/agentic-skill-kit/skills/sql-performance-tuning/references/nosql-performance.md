# NoSQL Performance (MongoDB 7, Redis 7, DynamoDB, Cosmos DB)

## MongoDB

### Evidence
| What | How |
|---|---|
| Plan + stats | `db.awb_event.find({...}).sort({...}).explain("executionStats")`; aggregations: `db.c.explain("executionStats").aggregate([...])` |
| Slow ops | Profiler `db.setProfilingLevel(1, { slowms: 100 })` → `db.system.profile` (overhead; sample with `sampleRate`); slow query log in `mongod.log` |
| Running now | `db.currentOp({ secs_running: { $gt: 5 } })` / `$currentOp` aggregation |
| Index use | `db.c.aggregate([{ $indexStats: {} }])` (`accesses.ops` since restart) |
| Atlas | Performance Advisor, Query Profiler (suggestions: verify like SQL Server DMVs) |

### Reading explain
| Field | Good | Red flag |
|---|---|---|
| `winningPlan.stage` | `IXSCAN` → `FETCH` | `COLLSCAN` on a large collection |
| `totalKeysExamined` : `totalDocsExamined` : `nReturned` | ≈ 1 : 1 : 1 | Docs examined ≫ returned → index not selective / missing fields |
| `SORT` stage (in-memory) | Absent (index provides order) | `SORT` present; 100 MB blocking-sort limit → `allowDiskUse` spill (default on in 6.0+) |
| `PROJECTION_COVERED` | Covered query, no FETCH | — |
| `rejectedPlans` | Few | Many similar indexes → plan-cache churn; drop redundant ones |

### Index design: ESR rule
Compound index order: **E**quality fields → **S**ort fields → **R**ange fields.
```js
// Query: open shipments for a station, newest first, last 7 days
db.shipment.find({ station: "DXB", status: "OPEN", createdAt: { $gte: ISODate("2026-09-20") } })
           .sort({ createdAt: -1 })
db.shipment.createIndex({ station: 1, status: 1, createdAt: -1 })   // E, E, S+R on same field
```
- Partial indexes (`partialFilterExpression: { status: "OPEN" }`) for hot subsets; TTL indexes for scan/event expiry.
- Each index costs RAM (working set) and write amplification; target: indexes fit in WiredTiger cache.
- Build on live replica sets: 4.2+ builds are online-ish (brief locks at start/end); do rolling builds for very large collections.
- Hints (`.hint()`) only as a last resort; they freeze plan choice.

### Aggregation pipeline order
| Rule | Why |
|---|---|
| `$match` first (and `$sort` + `$limit` early) | Only the first `$match`/`$sort` can use an index |
| `$project`/`$unset` unneeded fields early | Less memory per stage (100 MB per stage limit; `allowDiskUse`) |
| `$lookup` after filtering; index the `foreignField` | `$lookup` runs per input doc: N+1 inside the DB |
| Avoid `$unwind` on huge arrays then `$group` | Explodes doc count; model events as separate docs / bucket pattern |
| `$facet` sub-pipelines cannot use indexes | Filter before `$facet` |

### Common causes
Unbounded arrays (tracking events inside shipment doc) → document growth and 16 MB limit; `$regex` without anchored prefix; `$ne`/`$nin` (non-selective); `skip()` deep paging → range on `_id`/`createdAt`; read preference secondary returning stale data mistaken for bugs.

## Redis

| Problem | Detect | Fix |
|---|---|---|
| Slow commands | `SLOWLOG GET 20`, `LATENCY DOCTOR`, `INFO commandstats` | Replace O(N) commands: `KEYS` → `SCAN`; `HGETALL`/`SMEMBERS` on big keys → `HSCAN`/`SSCAN` or split |
| Big keys | `redis-cli --bigkeys`, `--memkeys`, `MEMORY USAGE key` | Split (hash per flight/day), cap list length (`LTRIM`), `UNLINK` instead of `DEL` (async free) |
| Hot keys | `redis-cli --hotkeys` (needs LFU `maxmemory-policy`), client-side metrics, `MONITOR` briefly (**Heavy**) | Local in-process cache with short TTL, replicate key (`key:{n}` shards) and read randomly, read replicas |
| Cluster hot slot | Per-node ops/CPU skew | Hash tags `{...}` only where multi-key ops need them; otherwise spread keys |
| Evictions / OOM | `INFO stats` `evicted_keys`, `INFO memory` | TTLs on cache keys, right `maxmemory-policy` (`allkeys-lfu` for caches), memory sizing |
| Round trips | High ops count, low CPU | Pipelining, `MGET`, Lua/functions for atomic multi-step |
| Stampede on expiry | Spikes when popular key expires | TTL jitter, lock/single-flight refresh, stale-while-revalidate |
| Persistence stalls | `latest_fork_usec`, AOF `fsync` | `appendfsync everysec`, avoid huge instances forking |

Redis is single-threaded for commands: one slow `O(N)` call blocks everyone.

## DynamoDB

| Problem | Detect | Fix |
|---|---|---|
| Hot partition | Throttling (`ThrottledRequests`) while table-level consumption is low; CloudWatch Contributor Insights | High-cardinality PK (AWB number, not station or date); write sharding (`FLIGHT#EK203#2026-09-27#<0..9>`) and scatter-gather reads |
| Scans | `Scan` in code / high consumed RCUs per item returned | Query on PK/SK; GSI for alternate access (GSI with low-cardinality PK is itself a hot spot) |
| Big items | Item size near 400 KB; RCU = 4 KB units, WCU = 1 KB units | Store payload in S3, keep pointer; split events into separate items |
| Capacity | Provisioned vs on-demand; adaptive capacity; per-partition limits 3 000 RCU / 1 000 WCU | On-demand for spiky loads; provisioned + auto scaling for steady |
| GSI back-pressure | GSI throttled throttles base writes | Provision GSI capacity ≥ base write rate; sparse GSIs |
| Consistency cost | Strongly consistent reads = 2× eventual RCU | Eventual where acceptable |

## Cosmos DB

| Problem | Detect | Fix |
|---|---|---|
| Hot logical partition | 429s with low total RU; "Normalized RU Consumption" at 100% on one partition key range | Higher-cardinality partition key (`/awbNo`), synthetic key (`/stationDay` + suffix), hierarchical partition keys |
| Cross-partition queries | Query metrics: many partitions touched, high RU | Include partition key in filter; point reads (`ReadItem` by id + pk ≈ 1 RU per 1 KB) |
| High RU per query | `x-ms-request-charge` header, query metrics | Composite indexes for `ORDER BY` on multiple fields; exclude unused paths from indexing policy (lowers write RU) |
| Logical partition limit | 20 GB per logical partition | Re-key before hitting it |
| Consistency level | Strong/bounded staleness cost more RU and latency | Session consistency (default) for most apps |

## Measurement
Mongo: `executionTimeMillis`, keys/docs examined, p95 from profiler. Redis: `LATENCY HISTORY`, ops/s, hit ratio (`keyspace_hits / (hits + misses)`). DynamoDB: consumed capacity (`ReturnConsumedCapacity: TOTAL`), throttles, p99 latency. Cosmos: RU charge per operation, 429 rate, p99.
