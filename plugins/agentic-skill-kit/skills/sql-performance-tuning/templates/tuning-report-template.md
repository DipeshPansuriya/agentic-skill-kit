# Tuning Report: short query name (e.g. "DXB station event feed")

**Engine / version:** SQL Server 2022 (compat 160) | PostgreSQL 16.x | MongoDB 7.0 (state how known: `@@VERSION` / `version()` / assumed)  
**Scope:** query / procedure / collection, caller (API, report, batch), how often it runs  
**Target:** e.g. p95 under 300 ms at 50 calls/min; or "reduce logical reads 10×"  
**Assumptions:** volumes, parameters used, environment (prod / staging copy), cache state

## 1. Summary
Two to four sentences: root cause, the top fix, expected effect (labelled "expected, verify"), and risk.

## 2. Evidence
| Item | Value | Source |
|---|---|---|
| Query text + slow parameters | `@station = N'DXB'`, `@from = 2026-09-01` | App log / Query Store |
| Plan | Actual plan, file name / plan hash / queryid | SSMS / `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)` |
| Row counts | `awb_event` ≈ 12 M, `shipment` ≈ 2.4 M | `sys.partitions` / `pg_class.reltuples` |
| Statistics age | last updated, modification counter | `sys.dm_db_stats_properties` / `pg_stat_user_tables` |
| Waits / blocking | top waits during the slow window | `sys.dm_exec_session_wait_stats` / `pg_stat_activity` |
| Analyzer output | paste `scripts/plan_analyzer.py` table; mark Confirmed / False positive | script |
| Lint output | paste `scripts/sql_lint.py` output (if SQL text given) | script |
| Missing | what was not provided + exact command to get it | — |

## 3. Findings
Severity: **High** = main cause of the slowness, wrong results, or outage/blocking risk · **Medium** = measurable cost at current volume · **Low** = minor / future risk.

| # | Severity | Issue | Evidence (plan node / metric) | Fix | Expected gain | Risk |
|---|---|---|---|---|---|---|
| 1 | High | Implicit conversion forces scan | Node 2 Clustered Index Scan, 12 M rows read for 185 k returned; `CONVERT_IMPLICIT(nvarchar(3),[station])` | Type `@station` as `VARCHAR(3)` in the app / `sp_executesql` | Seek instead of scan once an index on `station` exists (expected, verify) | None for results; app change + deploy |
| 2 | High | No index for station + time filter | Same node; missing-index hint (verify) suggests `event_ts` | `CREATE INDEX ix_awb_event_station_ts ON dbo.awb_event (station, event_ts DESC) INCLUDE (awb_no, status_code) WITH (ONLINE = ON);` Serves this query only; equality `station` first, then range/sort `event_ts` | Reads ~150 k pages → low thousands (expected, verify) | +1 index write per insert on a 12 M-row hot table; ~X GB; online build needs Enterprise/Azure |
| 3 | Medium | Sort spill | Node 0 SortSpillDetails, 6 210 pages written to tempdb; est 2 100 vs actual 185 000 | Fixed by #1/#2 (index provides order, estimate corrects) | Spill gone | — |

Rules: every index row names the query it serves, the key order reason, and write + storage cost. Missing-index hints are marked "verify".

## 4. Changes
```sql
-- Rewritten query / typed parameters (full text)
```
```sql
-- Index DDL (online / CONCURRENTLY), marked Heavy if large
```

## 5. Before / After measurement plan
| Metric | Before (measured) | After (to measure) | How |
|---|---|---|---|
| Duration p50 / p95 | 7.3 s / 9.1 s | | ≥ 3 runs, same parameters; Query Store / pg_stat_statements delta |
| Logical reads / shared buffers | 1 295 210 (148 210 scan + 1 147 000 seek/lookup) | | `SET STATISTICS IO ON` / `EXPLAIN (ANALYZE, BUFFERS)` |
| CPU ms | 6 981 | | `SET STATISTICS TIME ON` / plan |
| Est vs actual rows (worst node) | 2 100 vs 185 000 | | Actual plan |
| Spills / temp | 6 210 pages | | Plan warnings / `temp_blks_written` |
| Write impact (new index) | insert rate, index size = n/a | | `sys.dm_db_partition_stats` / `pg_relation_size` |

Test with the slow parameters **and** a typical small-station value. Production check window: e.g. 24 h including the night import.

## 6. Rollback
| Change | Rollback | Lock / impact |
|---|---|---|
| New index | `DROP INDEX ix_awb_event_station_ts ON dbo.awb_event;` / `DROP INDEX CONCURRENTLY ...` | Brief schema lock |
| Parameter type change | Revert app commit | Deploy |
| Statistics update | Not needed (re-run later) | IO during update |
| Query Store forced plan | `EXEC sp_query_store_unforce_plan @query_id, @plan_id;` | None |

## 7. Needs input / next steps
- Anything missing (actual plan, row counts, version) and who provides it.
- Statements that need confirmation before running (**Heavy** / **Destructive**).
