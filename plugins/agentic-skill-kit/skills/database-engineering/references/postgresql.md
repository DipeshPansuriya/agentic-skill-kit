# PostgreSQL (16+)

## Reading EXPLAIN (ANALYZE, BUFFERS)
Run: `EXPLAIN (ANALYZE, BUFFERS, SETTINGS) <query>;` (**ANALYZE executes the query**: wrap DML in `BEGIN; ... ROLLBACK;`). PG16 adds `GENERIC_PLAN` for parameterised text; PG17 adds `SERIALIZE` and `MEMORY`.

| Look at | Meaning | Red flag |
|---|---|---|
| `actual time=a..b` | Per-loop ms to first/last row | Multiply by `loops` |
| `rows=` estimated vs actual | Planner accuracy | Off by 10×+ → stale stats, correlated columns, functions on columns |
| `Buffers: shared hit / read` | Pages from cache / disk (8 kB each) | Large `read` → I/O bound; large `hit` on few rows → poor selectivity |
| `Rows Removed by Filter` | Rows read then discarded | High vs returned → missing/unsuitable index |
| `Seq Scan` | Full table read | Fine for small tables or >~5-10% of rows; bad on a hot big-table lookup |
| `Nested Loop` with large outer `loops` | N index probes | Bad when estimate said 1 row and actual is 100k |
| `Sort Method: external merge Disk` | Spilled to disk | Raise `work_mem` for the session, or index the sort order |
| `Hash ... Batches: >1` | Hash spilled | `work_mem`, or reduce rows before join |
| `Heap Fetches` on Index Only Scan | Visibility map not current | VACUUM the table |

Fix estimation problems with `ANALYZE tbl`, higher `ALTER TABLE ... ALTER COLUMN ... SET STATISTICS 1000`, or extended statistics: `CREATE STATISTICS s (dependencies, ndistinct) ON origin, dest FROM shipment;`.

## Index types
| Type | Use for | Example |
|---|---|---|
| B-tree (default) | `=`, ranges, `ORDER BY`, prefix `LIKE 'abc%'` (needs `text_pattern_ops` unless C collation) | `CREATE INDEX ON awb_event (awb_no, event_ts DESC);` |
| Partial | Hot subset | `CREATE INDEX ON shipment (created_at) WHERE status <> 'DLV';` (query must repeat the predicate) |
| Covering (`INCLUDE`) | Index-only scans | `CREATE INDEX ON awb_event (awb_no) INCLUDE (status_code, event_ts);` |
| Expression | Queries on a function | `CREATE INDEX ON customer (lower(email));` |
| GIN | JSONB containment, arrays, full text, trigram | `CREATE INDEX ON msg USING gin (payload jsonb_path_ops);` · `USING gin (awb_no gin_trgm_ops)` for `LIKE '%123%'` (pg_trgm) |
| BRIN | Huge append-only tables where value correlates with physical order (timestamps) | `CREATE INDEX ON uld_scan USING brin (scan_ts);` tiny, lossy |
| GiST / SP-GiST | Ranges, geometry, exclusion constraints | `EXCLUDE USING gist (dock_id WITH =, slot WITH &&)` (needs btree_gist) |
| Hash | Equality only | Rarely better than B-tree |

- Multicolumn order: equality columns first, then range/sort column.
- Build on live tables with `CREATE INDEX CONCURRENTLY` (not in a transaction; on failure leaves an INVALID index to drop).
- Find unused indexes: `pg_stat_user_indexes.idx_scan = 0` (check since last stats reset, and replicas).
- Write cost: every index adds work to each INSERT and non-HOT UPDATE, plus WAL and vacuum; also blocks HOT updates if it covers updated columns.

## Partitioning (declarative)
- Use for time-series event tables (`awb_event`, `uld_scan`) above ~100 GB or when you need cheap retention (`DROP`/`DETACH PARTITION ... CONCURRENTLY`).
- `PARTITION BY RANGE (event_ts)`, monthly or daily; create future partitions ahead (pg_partman or a job) and keep a `DEFAULT` partition monitored.
- Queries must filter on the partition key to get pruning (check `Subplans Removed` in the plan).
- PK/unique constraints must include the partition key.
- Too many partitions (thousands) slows planning; aim for tens to low hundreds.

## JSONB
- Good for variable message payloads (Cargo-IMP/XML converted, carrier-specific attributes); bad for fields you filter/join on constantly: promote those to columns (optionally `GENERATED ALWAYS AS (payload->>'awb') STORED`).
- Operators: `->` json, `->>` text, `@>` containment (GIN-indexable), `?` key exists, `jsonb_path_query` for SQL/JSON path. PG16 adds `IS JSON`; PG17 adds `JSON_TABLE`.
- `jsonb_path_ops` GIN: smaller/faster, supports `@>` only. Default `jsonb_ops` supports `?`, `?|`, `?&` too.
- Updating one key rewrites the whole value (and TOAST): large, frequently changing documents are expensive.

## VACUUM and autovacuum
- MVCC leaves dead tuples; autovacuum reclaims them and updates the visibility map and stats.
- Symptoms of lag: bloat, slow index-only scans, `n_dead_tup` high in `pg_stat_user_tables`, wraparound warnings.
- For large hot tables, tune per table instead of globally:
  `ALTER TABLE awb_event SET (autovacuum_vacuum_scale_factor = 0.01, autovacuum_analyze_scale_factor = 0.005);`
- Long-running transactions and idle-in-transaction sessions and stale replication slots block cleanup: check `pg_stat_activity` (`xact_start`, `state`) and `pg_replication_slots`; set `idle_in_transaction_session_timeout`.
- `VACUUM FULL` takes an ACCESS EXCLUSIVE lock and rewrites the table: avoid online; use `pg_repack` instead.
- Watch wraparound: `SELECT relname, age(relfrozenxid) FROM pg_class WHERE relkind='r' ORDER BY 2 DESC LIMIT 10;`

## Locking
- Readers never block writers (MVCC). Row locks: `FOR UPDATE`, `FOR NO KEY UPDATE`, `SKIP LOCKED` (job queues).
- DDL takes ACCESS EXCLUSIVE; even a fast `ALTER` waits behind long queries and then blocks everyone queued behind it. Always `SET lock_timeout = '3s';` before DDL and retry.
- Safe-ish online changes: `ADD COLUMN` with a constant default (no rewrite since PG11); `ADD CONSTRAINT ... NOT VALID` then `VALIDATE CONSTRAINT` (weaker lock); `SET NOT NULL` via a validated `CHECK (col IS NOT NULL)` first (PG12+ skips the scan).
- Rewrites (avoid online): changing column type (most), `ADD COLUMN ... DEFAULT volatile_fn()`.
- Blocking chains: `SELECT pid, pg_blocking_pids(pid), wait_event_type, query FROM pg_stat_activity WHERE cardinality(pg_blocking_pids(pid)) > 0;`
- Deadlocks: access rows in a consistent order.

## pg_stat_statements
Enable via `shared_preload_libraries = 'pg_stat_statements'`, then `CREATE EXTENSION pg_stat_statements;`
```sql
SELECT queryid, calls, round(total_exec_time) AS total_ms, round(mean_exec_time,1) AS mean_ms,
       rows, shared_blks_read, left(query, 120) AS query
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 20;
```
Rank by **total** time (what costs the server) and by **mean** (what users feel). Use `auto_explain` (`auto_explain.log_min_duration`) to capture plans of slow statements in production.

## Connection pooling
- Each connection is a process (~several MB); hundreds of idle app connections hurt. Keep `max_connections` modest and pool.
- PgBouncer **transaction** mode for most apps: no session state across transactions (session `SET`, advisory session locks, `LISTEN`, and named prepared statements unless PgBouncer 1.21+ `max_prepared_statements`).
- App-side pools (HikariCP, Npgsql, SQLAlchemy): size ≈ a few × CPU cores of the DB, not the number of app threads.
- Set `statement_timeout` per role/app to cap runaway queries.

## Useful config starting points (verify for your hardware)
`shared_buffers` ≈ 25% RAM · `effective_cache_size` ≈ 50–75% RAM · `random_page_cost` 1.1 on SSD · `work_mem` per sort/hash node (multiply by concurrency) · `maintenance_work_mem` 1–2 GB for index builds.
