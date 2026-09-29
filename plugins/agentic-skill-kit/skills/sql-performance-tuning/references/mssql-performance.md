# SQL Server Performance (2019 / 2022, Azure SQL)

## 1. Capture evidence
| What | How | Notes |
|---|---|---|
| Actual plan | SSMS "Include Actual Execution Plan" (Ctrl+M), or `SET STATISTICS XML ON;` → save as `.sqlplan` | Actual rows, executions, spills, memory grant, warnings. Estimated plan lacks these |
| Reads / CPU | `SET STATISTICS IO, TIME ON;` | Compare **logical reads** per table before/after; elapsed time varies with cache/load |
| Last actual plan from cache (2019+) | `sys.dm_exec_query_plan_stats(plan_handle)` with `LAST_QUERY_PLAN_STATS = ON` (db scoped config) | Light-weight profiling; no need to re-run |
| Live progress | `sys.dm_exec_query_profiles` (lightweight profiling on by default in 2019+) | For a query still running |
| History | Query Store: Top Resource Consuming, Regressed Queries, Queries With Forced Plans | On by default for new DBs in 2022; check `actual_state_desc` is READ_WRITE |
| Environment | `SELECT @@VERSION;` + `SELECT compatibility_level FROM sys.databases WHERE name = DB_NAME();` | Compat level gates IQP features (160 = 2022) |

Heavy: `DBCC DROPCLEANBUFFERS` / `DBCC FREEPROCCACHE` affect the whole instance. Never on production; use a test copy for cold-cache timing.

## 2. Find expensive queries
```sql
-- Top 20 by total CPU since plan cached (resets on restart / plan eviction)
SELECT TOP (20)
       qs.total_worker_time / 1000        AS total_cpu_ms,
       qs.execution_count,
       qs.total_worker_time / qs.execution_count / 1000 AS avg_cpu_ms,
       qs.total_logical_reads / qs.execution_count      AS avg_reads,
       qs.total_elapsed_time / qs.execution_count / 1000 AS avg_elapsed_ms,
       qs.query_hash,
       SUBSTRING(st.text, qs.statement_start_offset/2 + 1,
         (CASE qs.statement_end_offset WHEN -1 THEN DATALENGTH(st.text) ELSE qs.statement_end_offset END
          - qs.statement_start_offset)/2 + 1) AS stmt
FROM sys.dm_exec_query_stats AS qs
CROSS APPLY sys.dm_exec_sql_text(qs.sql_handle) AS st
ORDER BY qs.total_worker_time DESC;
```
- Swap `ORDER BY` to `total_logical_reads` (IO) or `total_elapsed_time` (user pain). Group by `query_hash` for ad-hoc SQL with different literals.
- Query Store equivalent: `sys.query_store_runtime_stats` joined to `sys.query_store_plan` / `sys.query_store_query`; survives restarts and shows plan changes over time.

## 3. Waits: working or waiting?
```sql
SELECT TOP (15) wait_type, wait_time_ms, signal_wait_time_ms, waiting_tasks_count
FROM sys.dm_os_wait_stats
WHERE wait_type NOT IN ('SLEEP_TASK','BROKER_TASK_STOP','LAZYWRITER_SLEEP','SQLTRACE_BUFFER_FLUSH',
      'XE_TIMER_EVENT','XE_DISPATCHER_WAIT','REQUEST_FOR_DEADLOCK_SEARCH','CHECKPOINT_QUEUE',
      'HADR_FILESTREAM_IOMGR_IOCOMPLETION','DIRTY_PAGE_POLL','SP_SERVER_DIAGNOSTICS_SLEEP',
      'WAITFOR','LOGMGR_QUEUE','BROKER_TO_FLUSH','SOS_WORK_DISPATCHER')
ORDER BY wait_time_ms DESC;
```
Cumulative since restart: take two snapshots and diff. Per session: `sys.dm_exec_session_wait_stats`. Query Store 2017+ also stores wait categories per query.

| Wait | Usually means | First look |
|---|---|---|
| `PAGEIOLATCH_*` | Reading pages from disk | Scans that should be seeks; then IO latency (`sys.dm_io_virtual_file_stats`) |
| `LCK_M_*` | Blocking | Blocking chain, long transactions, missing index on the UPDATE/DELETE predicate |
| `CXPACKET` / `CXCONSUMER` | Parallelism (often benign) | Skewed parallel plans; MAXDOP / cost threshold only after plan review |
| `SOS_SCHEDULER_YIELD` | CPU pressure | Top CPU queries, scans in loops, scalar UDFs |
| `RESOURCE_SEMAPHORE` | Waiting for memory grant | Oversized grants from bad estimates, huge sorts/hashes |
| `WRITELOG` | Log flush latency | Tiny transactions in a loop (commit per row), log disk |
| `PAGELATCH_*` on tempdb pages 2:1:1 etc. | tempdb allocation contention | Multiple equal tempdb files; 2019+ memory-optimized tempdb metadata |
| `ASYNC_NETWORK_IO` | Client is slow to consume rows | App reading row-by-row / fetching huge result sets |

## 4. Reading the plan
Read right-to-left (data flow), start at the operator with the highest **actual** cost / elapsed (2014 SP2+ showplan has per-operator `ActualElapsedms` in `RunTimeCountersPerThread`).

| Operator / warning | Red flag | Fix |
|---|---|---|
| Estimated vs Actual Rows | ≥ 10× apart | Stats, SARGability, table variables, local variables, multi-statement TVFs |
| Clustered Index Scan / Table Scan | Big table, selective predicate, many rows read vs returned | SARGable rewrite; index on predicate |
| Key Lookup / RID Lookup | Actual executions in thousands+ | `INCLUDE` the looked-up columns if the query is hot and columns are few |
| Nested Loops | Inner side executed ≫ estimated | Estimate fix; hash join becomes possible |
| Sort / Hash Match with warning | `SpillToTempDb` / `HashSpillDetails` / `SortSpillDetails` | Better estimates; memory grant feedback (2019+ row mode); index for order |
| `PlanAffectingConvert` / `CONVERT_IMPLICIT(... [column])` | Type mismatch on the column side | Match parameter type (`VARCHAR` vs `NVARCHAR`) |
| `MissingIndexes` element | Optimizer's per-query wish | Verify (see §6) |
| Excessive memory grant | `GrantedMemory` ≫ `MaxUsedMemory` | Over-estimation; wide `VARCHAR(MAX)` columns in sorts |
| Filter operator late in plan | Predicate applied after join | Rewrite so it can be pushed down (non-SARGable function, UDF) |

## 5. SARGability and implicit conversions
- Non-SARGable: function/arithmetic on the column (`YEAR(col)`, `ISNULL(col,..)`, `col + 1 = @x`), leading wildcard `LIKE '%x'`, mismatched types. Rewrites in `anti-patterns.md`.
- Data type precedence: `NVARCHAR` > `VARCHAR`. `WHERE awb_no = N'17612345675'` on a `VARCHAR` column converts the **column** → scan (with SQL collation) or a less efficient range seek (Windows collation). .NET `SqlParameter` / EF strings default to `NVARCHAR`; set `DbType.AnsiString` / `HasColumnType("varchar(12)")`.
- Casting `datetime` → `date` is SARGable (dynamic range seek) but a plain range is clearer and portable.

## 6. Missing-index DMVs (caveats)
```sql
SELECT TOP (20) d.statement AS table_name, d.equality_columns, d.inequality_columns, d.included_columns,
       s.user_seeks, s.avg_total_user_cost, s.avg_user_impact
FROM sys.dm_db_missing_index_details d
JOIN sys.dm_db_missing_index_groups g ON g.index_handle = d.index_handle
JOIN sys.dm_db_missing_index_group_stats s ON s.group_handle = g.index_group_handle
ORDER BY s.user_seeks * s.avg_total_user_cost * s.avg_user_impact DESC;
```
Caveats: reset on restart/failover and on metadata changes; no column order within equality/inequality lists (you choose); ignores sort order and existing near-duplicate indexes; suggests wide `INCLUDE` lists; never considers write cost; max 600 groups. 2019+: `sys.dm_db_missing_index_group_stats_query` links suggestions to query hashes. Treat every row as "verify": find the query, check existing indexes (`sys.indexes` + `sys.index_columns`), then design.

Index usage vs cost:
```sql
SELECT OBJECT_NAME(i.object_id) AS tbl, i.name, s.user_seeks, s.user_scans, s.user_lookups, s.user_updates
FROM sys.indexes i LEFT JOIN sys.dm_db_index_usage_stats s
  ON s.object_id = i.object_id AND s.index_id = i.index_id AND s.database_id = DB_ID()
WHERE OBJECTPROPERTY(i.object_id,'IsUserTable') = 1
ORDER BY s.user_updates DESC;   -- high updates + zero reads = pure write cost
```

## 7. Parameter sniffing
Plan compiled for the first parameter values is reused; skewed columns (hub station `DXB` = 40% of rows vs `IXE` = 0.01%) make it bad for others.

| Option | When | Cost / caveat |
|---|---|---|
| **PSP optimization** (2022, compat 160) | Equality predicates on skewed columns | Automatic; up to 3 plan variants; check `sys.query_store_query_variant` |
| `OPTION (RECOMPILE)` | Infrequent, expensive, highly variable queries | Compile CPU on every run; plan not cached for reuse |
| `OPTION (OPTIMIZE FOR (@p = 'X'))` | One representative value is good for all | Bad for outliers; must be maintained |
| `OPTIMIZE FOR UNKNOWN` | Average-density plan acceptable | Same as local-variable trick; mediocre for everyone |
| Query Store plan forcing / hints (2022 `sys.sp_query_store_set_hints`) | Known-good plan exists; cannot change code | Forcing can fail after schema changes; monitor |
| Split branches / procedures | Few distinct shapes (big hub vs small station) | More code |

"Fast in SSMS, slow in app": SSMS defaults `SET ARITHABORT ON`, ADO.NET OFF → separate cache entries, so SSMS compiles a fresh plan. Compare by `query_hash` in Query Store, not by re-running in SSMS.

## 8. Blocking, deadlocks, RCSI
- Blocking now: `sys.dm_exec_requests` (`blocking_session_id`, `wait_type`, `wait_resource`) + `sys.dm_tran_locks`. Fix the head blocker (open transaction, missing index on the UPDATE predicate causing scans and wide locks).
- Deadlocks: `system_health` XE session → `xml_deadlock_report`. Fixes: consistent object access order, shorter transactions, index so UPDATE/DELETE seeks instead of scanning, RCSI for reader/writer deadlocks. Add retry for error 1205 in the app.
- Lock escalation at ~5 000 locks per statement → table lock. Batch DML below that.
- **RCSI** (`ALTER DATABASE x SET READ_COMMITTED_SNAPSHOT ON WITH ROLLBACK IMMEDIATE` — needs exclusive access; **Heavy**, schedule it): readers stop blocking writers. Cost: version store in tempdb (2019+ ADR uses the persistent version store in the user DB), 14 bytes per row version tag. Review code relying on blocking reads (queue tables → `UPDLOCK, READPAST`).
- `NOLOCK` is not a fix: dirty, missing and duplicate rows.

## 9. tempdb and memory grants
- Spills: `Sort Warnings` / `Hash Warnings` XE events or plan warnings. Cause is usually under-estimation → fix estimates first.
- Memory grant feedback (row mode 2019+, percentile + persistence 2022) adjusts repeated queries automatically.
- tempdb: multiple equal-size data files (1 per core up to 8), trace flags 1117/1118 behaviour default since 2016.

## 10. Index maintenance myths
| Myth | Reality |
|---|---|
| "Rebuild everything nightly at 30% fragmentation" | On SSD/SAN, logical fragmentation rarely matters for seeks; rebuilds cost log, IO, blocking (offline) and AG traffic. Page **density** (`avg_page_space_used_in_percent`) matters more |
| "The rebuild fixed performance" | It usually updated statistics with FULLSCAN and evicted the bad plan. Try `UPDATE STATISTICS` first |
| "Add the missing index hint" | See §6 |
| "More indexes = faster" | Every index costs every INSERT/DELETE and relevant UPDATE, plus log, backup, AG and memory |
| "Shrink the database to reclaim space" | Shrink fragments indexes badly; avoid except after one-off purge |

Use `ALTER INDEX ... REORGANIZE` / `REBUILD WITH (ONLINE = ON, RESUMABLE = ON)` (Enterprise/Azure) only with measured need.

## 11. Statistics
- Auto-update threshold is dynamic (≈ √(1000 × rows)) at compat ≥ 130; append-only event tables still get ascending-key problems (new dates beyond histogram). 2014+ CE handles this better; check with the plan.
- After big loads: `UPDATE STATISTICS dbo.awb_event WITH SAMPLE 10 PERCENT` or `FULLSCAN` off-peak (**Heavy** on huge tables). `PERSIST_SAMPLE_PERCENT = ON` keeps your sample.
- Filtered statistics for skewed subsets; `sys.dm_db_stats_properties` for `last_updated` and `modification_counter`.

## 12. Other engine features worth checking
- Scalar UDF inlining (2019+, compat 150): check `sys.sql_modules.is_inlineable`; non-inlineable UDFs run per row and block parallelism.
- Table variable deferred compilation (2019+): correct cardinality at first compile.
- Batch mode on rowstore (2019+) for analytic queries; columnstore for large event aggregates.
- Partitioning: aligned indexes, partition elimination needs the partition column in the predicate with a compatible type; `SWITCH` for fast retention.
- Optimized locking (Azure SQL / 2025) reduces lock memory and blocking; version-gated.
