# SQL Server / T-SQL (2019–2022, Azure SQL)

## Execution plans
- Get the **actual** plan (SSMS "Include Actual Execution Plan", or `SET STATISTICS XML ON`), plus `SET STATISTICS IO, TIME ON` for logical reads and CPU.
- From production history: Query Store (`sys.query_store_runtime_stats`, "Top Resource Consuming Queries"); on by default in SQL Server 2022 for new databases.
- Read right-to-left, top-to-bottom. Check, in order:

| Look at | Red flag | Usual fix |
|---|---|---|
| Estimated vs Actual rows | 10×+ difference | Update stats, avoid non-SARGable predicates, table variables (pre-2019), local variables |
| Index/Clustered Index **Scan** on a big table for a selective filter | Missing index or non-SARGable predicate | Rewrite predicate; add index |
| **Key Lookup** with high executions | Index lacks columns | Add `INCLUDE` columns (if it pays off) |
| Warnings (yellow triangle) | Implicit conversion, spill to tempdb, missing stats | Fix data types; memory grant; stats |
| `CONVERT_IMPLICIT` on the column side | NVARCHAR parameter vs VARCHAR column → scan | Match parameter type to column |
| Parallelism + huge memory grant | Over-estimation | Better stats/rewrite |
| Missing index hint (green text) | A hint, not a plan | Evaluate against existing indexes; never create blindly |

## SARGability
A predicate is SARGable when the engine can seek an index on the column directly.

| Non-SARGable | SARGable rewrite |
|---|---|
| `WHERE YEAR(created_at) = 2026` | `WHERE created_at >= '2026-01-01' AND created_at < '2027-01-01'` |
| `WHERE CONVERT(date, event_ts) = @d` | Range on `event_ts` (casting datetime→date is actually SARGable in SQL Server, but a range is clearer and portable) |
| `WHERE LEFT(awb_no, 3) = '176'` | `WHERE awb_no LIKE '176%'` |
| `WHERE ISNULL(status, 'X') = 'X'` | `WHERE status = 'X' OR status IS NULL` |
| `WHERE qty * 2 > @n` | `WHERE qty > @n / 2.0` |
| `WHERE awb_no = @p` with `@p NVARCHAR`, column `VARCHAR` | Declare `@p VARCHAR(12)` |
| `WHERE UPPER(code) = 'LHR'` | Case-insensitive collation already ignores case; drop `UPPER` |
| `LIKE '%123'` | Full-text, a reversed computed column, or n-gram table |

## Parameter sniffing
The plan is compiled for the first parameter values seen and reused. Skewed data (one hub airport with 60% of shipments) makes the cached plan bad for others.
- Diagnose: same procedure fast in SSMS but slow in app (different `SET ARITHABORT` → different cache entry), or Query Store shows multiple plans with very different durations.
- Options, least to most invasive:
  1. SQL Server 2022 **Parameter Sensitive Plan optimisation** (compat level 160) keeps several plans automatically.
  2. `OPTION (RECOMPILE)` on the statement: good for infrequent, expensive queries.
  3. `OPTION (OPTIMIZE FOR (@hub = 'DXB'))` or `OPTIMIZE FOR UNKNOWN`.
  4. Force a known-good plan via Query Store (`sp_query_store_force_plan`).
  5. Split into separate procedures/branches for the skewed values.
- Avoid local-variable copying as a "fix": it gives density-based estimates for everyone.

## Indexes
- Clustered index = table order. Good key: narrow, unique, static, ever-increasing (`BIGINT IDENTITY`, or `(event_ts, event_id)` for event tables). Random GUIDs cause page splits: use `NEWSEQUENTIALID()` or keep GUID non-clustered.
- Non-clustered: key columns = seek/sort columns (equality first, then range); `INCLUDE` = selected columns to avoid key lookups.
- Filtered indexes: `CREATE INDEX ix_open ON dbo.shipment (created_at) WHERE status <> 'DLV';` (parameterised queries may not match; use `OPTION (RECOMPILE)` or literal).
- Columnstore (non-clustered or clustered) for analytics on large event tables; batch mode also applies to rowstore in 2019+.
- Online builds: `WITH (ONLINE = ON)` (Enterprise/Azure SQL); `RESUMABLE = ON` for very large indexes.
- Usage and missing-index DMVs: `sys.dm_db_index_usage_stats`, `sys.dm_db_missing_index_details` (reset on restart; treat as hints).
- Write cost: each non-clustered index is maintained on every INSERT/DELETE and on UPDATEs of its columns, adds log volume and lock footprint.
- Statistics: auto-update threshold on big tables is dynamic in compat ≥130; for skewed event tables schedule `UPDATE STATISTICS ... WITH FULLSCAN` or larger sample after big loads.

## Isolation and RCSI
| Level | Notes |
|---|---|
| READ COMMITTED (default, locking) | Readers take shared locks; readers and writers block each other |
| **RCSI** (`ALTER DATABASE x SET READ_COMMITTED_SNAPSHOT ON`) | Readers read the last committed version from tempdb version store; no reader/writer blocking. Default in Azure SQL Database. Costs tempdb space and a 14-byte row overhead. Check code that relies on blocking reads (e.g. "read then update" queue logic → use `UPDLOCK, READPAST`) |
| SNAPSHOT | Transaction-level consistency; update conflicts raise error 3960 → retry |
| READ UNCOMMITTED / `NOLOCK` | Dirty reads, missed and **duplicate** rows during page splits. Not a performance fix |
| SERIALIZABLE | Range locks; deadlock-prone; use only where needed |

- Deadlocks: capture with the `system_health` Extended Events session (`xml_deadlock_report`); fix by consistent access order, shorter transactions, covering indexes.
- Queue pattern: `WITH (ROWLOCK, UPDLOCK, READPAST)` + `TOP (n)` + `OUTPUT`.

## T-SQL notes
- `SET NOCOUNT ON;` and `SET XACT_ABORT ON;` at the top of procedures.
- Error handling: `BEGIN TRY ... BEGIN TRAN ... COMMIT ... END TRY BEGIN CATCH IF @@TRANCOUNT > 0 ROLLBACK; THROW; END CATCH`.
- Dynamic SQL: `EXEC sp_executesql @sql, N'@awb varchar(12)', @awb = @awb;` and `QUOTENAME()` for identifiers. Never `EXEC(@sql + @input)`.
- Temp tables (`#t`) have statistics; table variables get fixed low estimates (deferred compilation improves this in 2019+).
- `TOP` without `ORDER BY` returns arbitrary rows.
- `STRING_AGG`, `STRING_SPLIT` (2022: `enable_ordinal`), `GREATEST/LEAST`, `DATE_BUCKET`, `IS DISTINCT FROM` available in 2022.
