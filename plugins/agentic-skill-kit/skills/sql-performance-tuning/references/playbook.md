# Slow-Query Playbook

Work top to bottom; stop when the cause is proven. Measure before and after every change.

## 1. Define the problem
| Question | Why |
|---|---|
| Exact query text + the **slow** parameter values | Plans differ by parameter (sniffing, skew) |
| p50 / p95 duration, calls per minute | One slow run ≠ slow query; total load = mean × calls |
| Always slow or sometimes? | Sometimes → parameters, blocking, plan change, cold cache, concurrency |
| Since when; what changed (deploy, data growth, index, stats, upgrade, config) | Regressions have a trigger |
| Engine + version + edition / service tier | Features and fixes are version-gated |

## 2. Waiting or working?
| Engine | Check | If waiting |
|---|---|---|
| SQL Server | `sys.dm_exec_requests.wait_type`, `blocking_session_id`; Query Store waits | Blocking → fix head blocker; IO → scans; memory → grants |
| PostgreSQL | `pg_stat_activity.wait_event_type` (`Lock`, `IO`, `LWLock`, `Client`) | `Lock` → `pg_blocking_pids`; `IO` → reads/buffers |
| MongoDB | `$currentOp` `waitingForLock`, `numYields` | Long-running writes, missing index on update filter |
| Redis | `SLOWLOG`, `LATENCY DOCTOR` | One O(N) command blocks all |

A saturated server makes every query slow: check top consumers before tuning the one reported.

## 3. Symptom → cause → check → fix
| Symptom | Likely cause | Check | Fix (in rank order) |
|---|---|---|---|
| Full scan on big table, few rows returned | Missing index or non-SARGable predicate | Plan: Scan node, rows read ≫ returned | SARGable rewrite → index (with cost) |
| Estimated 1 row, actual 100 000 | Stale/insufficient stats, correlated columns, function on column, table variable | Estimated vs actual per node | Rewrite → stats (`ANALYZE`, `UPDATE STATISTICS`, extended stats) |
| Fast in SSMS, slow from app | Parameter sniffing; different `SET` options; `NVARCHAR` params | Query Store plans per query; `CONVERT_IMPLICIT` | Typed params → PSP / RECOMPILE / OPTIMIZE FOR / forcing |
| Fast for small station, slow for hub | Data skew + cached plan | Plan for each value | PSP (2022) / branches / `force_custom_plan` (PG) |
| Thousands of key lookups | Non-covering index | Key Lookup actual executions | `INCLUDE` columns if hot and narrow |
| Nested loop with huge inner executions | Under-estimated outer input | Actual loops vs estimate | Fix estimate; then join rewrite |
| Sort / hash spills | Memory grant too small (bad estimate) or `work_mem` low | SQL Server spill warnings; PG `external merge`, `Batches > 1`, `temp_blks_written` | Fix estimate → index for order → per-session memory |
| Slow gradually over months | Growth without index, bloat (PG), ascending-key stats | Table size trend, `n_dead_tup`, stats date | Index / VACUUM tuning / stats / partitioning |
| Slow right after deploy | New query shape, ORM change, N+1 | Top queries by `calls`; Query Store regressed | Rewrite / batch fetch in app |
| Page 5 000 of a list is slow | `OFFSET` deep paging | Rows read = offset + page | Keyset pagination |
| Timeouts at peak only | Blocking, lock escalation, connection pool exhaustion | Blocking chain, waits, pool metrics | Shorter transactions, batching, index for UPDATE predicate, RCSI |
| Deadlocks | Opposite access order, scans under UPDATE | Deadlock graph / PG log | Consistent order, seek indexes, retry logic |
| Large DELETE/UPDATE blocks everything | One giant transaction, escalation, log growth | Lock count, log usage | Batch 1 000–5 000 rows per transaction, keyed loop |
| COUNT(*) on huge table slow | Full scan by design | Plan | Estimates (`pg_class.reltuples`, `sys.partitions`) or counter table |
| OLTP query fast but `JIT` adds 200 ms | JIT on high-cost estimate | PG `JIT:` block | Fix estimate or `jit = off` per role |
| Mongo query slow | `COLLSCAN`, docs examined ≫ returned, in-memory `SORT` | `explain("executionStats")` | ESR compound index, `$match` first |
| DynamoDB / Cosmos throttling, low total usage | Hot partition key | Contributor Insights / normalized RU per partition | Higher-cardinality or sharded key |
| Redis latency spikes | Big key, `KEYS`, hot key, fork | `SLOWLOG`, `--bigkeys` | `SCAN`, split key, local cache |

## 4. N+1 from ORMs (seen at the DB)
- Signal: one statement with huge `calls` and tiny `rows_per_call` (pg_stat_statements) or huge `execution_count` (Query Store / `dm_exec_query_stats`), rising after a deploy.
- DB-side fix: provide a set-based query (`WHERE awb_no = ANY($1)` / TVP / `IN` with batches) and hand the app change to backend owners (EF `Include` / split queries, Hibernate `JOIN FETCH` / batch size).
- Also check ORM parameter types (`NVARCHAR` vs `VARCHAR`) and `SELECT *` entity loading.

## 5. Batching large DML
```sql
-- SQL Server: purge ULD scans older than cutoff in batches (Destructive: confirm, run off-peak)
DECLARE @cutoff datetime2 = '2024-01-01', @n int = 1;
WHILE @n > 0
BEGIN
    DELETE TOP (5000) FROM dbo.uld_scan WHERE scan_ts < @cutoff;   -- needs index on scan_ts
    SET @n = @@ROWCOUNT;
    WAITFOR DELAY '00:00:00.200';                                 -- let log/AG/replicas breathe
END;
```
```sql
-- PostgreSQL: keyed batches (Destructive: confirm, run off-peak)
WITH doomed AS (
  SELECT ctid FROM uld_scan WHERE scan_ts < '2024-01-01' LIMIT 5000
)
DELETE FROM uld_scan u USING doomed d WHERE u.ctid = d.ctid;   -- repeat until 0 rows; COMMIT between batches
```
Better for time-series retention: partition by time and `DROP`/`SWITCH`/`DETACH` whole partitions.

## 6. Fix ranking (always this order)
1. Rewrite · 2. Index · 3. Statistics · 4. Plan stability · 5. Schema (partitioning, summary tables) · 6. Config / hardware · 7. Architecture (cache, replicas)

## 7. Verify
- Same parameters (slow **and** typical), same cache state noted, ≥ 3 runs; compare reads/buffers first (stable), then time.
- Estimates now close to actuals; spills / lookups / scans gone as expected.
- Write impact of new indexes: insert rate, index size, log/WAL volume.
- Production: watch p95 and total time in Query Store / pg_stat_statements for a full business cycle (e.g. 24 h including the night import).
