# PostgreSQL Performance (16+)

## 1. Capture evidence
| What | How | Notes |
|---|---|---|
| Actual plan | `EXPLAIN (ANALYZE, BUFFERS, SETTINGS) SELECT ...;` | **Executes the query.** For DML: `BEGIN; EXPLAIN (ANALYZE, BUFFERS) UPDATE ...; ROLLBACK;` (still takes locks and writes WAL: **Heavy** on prod) |
| Machine-readable plan | add `FORMAT JSON` → feed to `scripts/plan_analyzer.py` | Same information, parseable |
| Plan without running | `EXPLAIN (GENERIC_PLAN) SELECT ... WHERE awb_no = $1;` (PG16+) | Estimates only |
| Extra detail | `WAL` (DML), `VERBOSE` (output columns), PG17 `SERIALIZE`, `MEMORY` | `SETTINGS` lists non-default planner settings |
| Environment | `SELECT version();` `SHOW work_mem;` etc. | Managed services (RDS, Azure Flexible) may cap settings |
| Timing overhead | `EXPLAIN (ANALYZE, TIMING OFF)` | Per-node timing can inflate runtimes of tiny loops |

## 2. Find expensive queries
```sql
-- needs shared_preload_libraries = 'pg_stat_statements' (restart) + CREATE EXTENSION pg_stat_statements;
SELECT queryid, calls,
       round(total_exec_time)       AS total_ms,
       round(mean_exec_time, 1)     AS mean_ms,
       round(stddev_exec_time, 1)   AS stddev_ms,
       rows / NULLIF(calls, 0)      AS rows_per_call,
       shared_blks_hit, shared_blks_read,
       temp_blks_written,            -- > 0 means sorts/hashes spilled
       left(query, 120)             AS query
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 20;
```
- Rank by **total** (server load), **mean** (user latency), **calls** (N+1 from ORMs: thousands of identical single-row SELECTs per request).
- High `stddev` vs `mean` → parameter-dependent plans or blocking.
- Reset for a clean before/after window: `SELECT pg_stat_statements_reset();` (clears for everyone: confirm first).
- **auto_explain** captures plans of slow statements in prod: `session_preload_libraries = 'auto_explain'`, `auto_explain.log_min_duration = '500ms'`, `auto_explain.log_analyze = on` (adds overhead to every statement: consider `auto_explain.sample_rate`), `log_buffers = on`, `log_format = json`.

## 3. Reading EXPLAIN ANALYZE
Start at the node with the largest **exclusive** time (node time minus children), bottom-up.

| Field / node | Meaning | Red flag → fix |
|---|---|---|
| `actual time=first..last rows=N loops=L` | Per loop; total = last × loops | Big `loops` on inner side of Nested Loop |
| `rows` estimated vs actual | Planner accuracy | ≥ 10× → `ANALYZE`, `SET STATISTICS`, extended stats, rewrite function-on-column |
| `Seq Scan` + `Rows Removed by Filter` | Rows read and discarded | Removed ≫ returned on a large table → index / partial index / rewrite |
| `Index Scan` + `Rows Removed by Filter` | Index finds, filter discards | Add filtered column to index or reorder |
| `Bitmap Heap Scan` `Recheck Cond`, `lossy` | Bitmap exceeded `work_mem` | Raise `work_mem` or narrow predicate |
| `Index Only Scan` `Heap Fetches: N` | Visibility map stale | VACUUM more often |
| `Sort Method: external merge Disk: NkB` | Sort spilled | Index providing the order, fewer rows/columns, session `work_mem` |
| `Hash ... Batches: N` (N > 1) | Hash spilled | `work_mem` / `hash_mem_multiplier`, filter earlier |
| `Memoize` `Evictions` | Cache too small | Usually OK; check estimate |
| `Buffers: shared read` high | Disk reads | Cold cache vs working set too large; index to read fewer pages |
| `Subplans Removed: N` / partitions listed | Partition pruning | All partitions scanned → predicate on partition key missing or wrong type |
| `JIT: ... Timing` | Compile time | JIT total ≫ query time on OLTP → `jit = off` for that role or raise `jit_above_cost` |
| `Planning Time` large | Many partitions, many joins | Reduce partitions, `join_collapse_limit`, prepared statements |

## 4. Row misestimates: causes and fixes
| Cause | Fix |
|---|---|
| Stale stats after bulk load | `ANALYZE awb_event;` (cheap, sample-based) |
| Skewed column (hub station) | `ALTER TABLE awb_event ALTER COLUMN station SET STATISTICS 1000; ANALYZE awb_event;` |
| Correlated columns (`origin`, `dest`; `carrier`, `flight_no`) | `CREATE STATISTICS st_route (dependencies, ndistinct, mcv) ON origin, dest FROM shipment; ANALYZE shipment;` |
| Function on column (`lower(email)`, `date(event_ts)`) | Expression index (also gets stats) or rewrite to a range |
| Generic plan for prepared statement | `plan_cache_mode = force_custom_plan` for that role/session; check with `EXPLAIN EXECUTE` |
| CTE / subquery boundaries | PG12+ inlines non-recursive, side-effect-free CTEs referenced once; `MATERIALIZED` forces a fence |

## 5. Indexes (always with query + cost)
| Type | Serves | Example |
|---|---|---|
| B-tree multicolumn | Equality cols first, then range/sort | `CREATE INDEX CONCURRENTLY ix_awb_event_awb_ts ON awb_event (awb_no, event_ts DESC);` |
| Covering `INCLUDE` (PG11+) | Index-only scan for hot lookups | `... ON awb_event (awb_no, event_ts DESC) INCLUDE (status_code);` |
| Partial | Hot subset of a big table | `CREATE INDEX CONCURRENTLY ix_ship_open ON shipment (created_at) WHERE status <> 'DLV';` (query must imply the predicate) |
| Expression | Function in predicate | `ON customer (lower(email))` |
| BRIN | Append-only time series correlated with physical order | `ON uld_scan USING brin (scan_ts)` (tiny; lossy; bad if rows updated/moved) |
| GIN | `jsonb @>`, arrays, full text, `pg_trgm` for `LIKE '%x%'` | `USING gin (payload jsonb_path_ops)` |

- `CREATE INDEX CONCURRENTLY`: no write block, slower, cannot run in a transaction, leaves an INVALID index on failure (`DROP INDEX CONCURRENTLY` it).
- Write cost: each index adds work to every INSERT and to non-HOT UPDATEs; indexing an updated column disables HOT for those updates, increasing bloat and WAL. Measure with `pg_relation_size('ix_name')` and insert throughput.
- Unused: `pg_stat_user_indexes.idx_scan = 0` (since `stats_reset`; check replicas too). Duplicates: same leading columns.

## 6. Memory: work_mem and spills
- `work_mem` is per sort/hash **node** per backend (and per parallel worker): 64 MB × 5 nodes × 200 connections = 64 GB worst case. Raise per session/role (`SET LOCAL work_mem = '256MB'` inside the report transaction), not globally.
- `hash_mem_multiplier` (default 2.0 in PG15+) gives hashes more room than sorts.
- Evidence: `temp_blks_written` in pg_stat_statements; `log_temp_files = 0` logs every temp file; plan `external merge` / `Batches`.

## 7. VACUUM, bloat, visibility
- Dead tuples: `SELECT relname, n_live_tup, n_dead_tup, last_autovacuum, last_autoanalyze FROM pg_stat_user_tables ORDER BY n_dead_tup DESC LIMIT 10;`
- Hot event tables: per-table `autovacuum_vacuum_scale_factor = 0.01`, `autovacuum_analyze_scale_factor = 0.005`; `autovacuum_vacuum_insert_scale_factor` (PG13+) keeps the visibility map fresh for insert-only tables.
- Blockers of cleanup: long transactions / `idle in transaction` (`pg_stat_activity.xact_start`), abandoned replication slots, prepared transactions.
- Bloat fix online: `pg_repack`; `VACUUM FULL` / `CLUSTER` take ACCESS EXCLUSIVE (**Heavy**). `REINDEX INDEX CONCURRENTLY` (PG12+) for bloated indexes.

## 8. Locks and blocking
```sql
SELECT a.pid, pg_blocking_pids(a.pid) AS blocked_by, a.wait_event_type, a.wait_event,
       now() - a.xact_start AS xact_age, a.state, left(a.query, 100) AS query
FROM pg_stat_activity a
WHERE a.state <> 'idle' AND (cardinality(pg_blocking_pids(a.pid)) > 0 OR a.xact_start < now() - interval '1 min')
ORDER BY xact_age DESC;
```
- Detail: `pg_locks` (`granted = false` rows are waiters). Deadlocks appear in the server log with both statements; fix with consistent row order (`ORDER BY id FOR UPDATE`), shorter transactions.
- DDL queues behind long reads then blocks everyone: `SET lock_timeout = '3s'` before DDL and retry.
- Queues: `FOR UPDATE SKIP LOCKED`.
- Guards: `statement_timeout`, `idle_in_transaction_session_timeout`, `lock_timeout` per role.

## 9. Partitioning for performance
- Pruning only when the query filters the partition key with a comparable type (plan-time or run-time pruning; check `Subplans Removed`).
- Benefits: smaller indexes per partition, cheap retention (`DETACH PARTITION ... CONCURRENTLY` PG14+, then `DROP`), partition-wise joins/aggregates (`enable_partitionwise_*`, off by default).
- Costs: planning time with many partitions; unique constraints must include the key; cross-partition queries scan every partition.

## 10. JIT and parallelism
- JIT (on by default since PG12) helps long analytic queries; on short OLTP queries with high estimated cost it can add 10s–100s of ms. Check the `JIT:` block; set `jit = off` or raise `jit_above_cost` per role.
- Parallel query: `max_parallel_workers_per_gather`; `Workers Planned` vs `Workers Launched` (fewer launched = worker pool exhausted).

## 11. Config starting points (only after plans)
`shared_buffers` ≈ 25% RAM · `effective_cache_size` 50–75% RAM · `random_page_cost = 1.1` on SSD · `effective_io_concurrency` 200 on SSD · `maintenance_work_mem` 1–2 GB · `max_connections` modest + PgBouncer. Change one at a time and measure.
