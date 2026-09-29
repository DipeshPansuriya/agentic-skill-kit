# Test Cases: sql-performance-tuning

Rerun after every edit. Score each with the 0–5 checklist.

## Quality checklist (1 point each, 0–5)
1. Engine + version + assumptions stated in line 1
2. Every finding cites evidence (plan node, metric, wait) or says exactly what to run to get it; nothing invented
3. Fixes ranked rewrite → index → statistics → config; no hardware blame without plan evidence
4. Rules respected: index with served query + write/storage cost; missing-index hints marked "verify"; heavy/destructive statements need confirmation
5. Before/after measurement plan and rollback present

## Cases
| # | Type | Request | Should trigger? | Expected |
|---|---|---|---|---|
| 1 | Single: MS-SQL | "This proc is fast in SSMS but slow from the .NET app" | Yes | Parameter sniffing + `ARITHABORT` cache entries; compare plans in Query Store; ranked options PSP (2022) → RECOMPILE → OPTIMIZE FOR → plan forcing; typed parameters |
| 2 | Single: MS-SQL + script | "Why is this slow?" + `templates/sample-plan-sqlserver.sqlplan` | Yes | Runs `scripts/plan_analyzer.py`; root cause = `CONVERT_IMPLICIT` on `station` → scan; fix param type first, then index `(station, event_ts DESC) INCLUDE (...)` with write cost; missing-index hint labelled verify; spill explained as consequence |
| 3 | Single: PG + script | "EXPLAIN ANALYZE attached, 8 s" + `templates/sample-plan-postgres.json` | Yes | Runs analyzer; root cause = `lower(station)` misestimate (1 200 vs 410 000) → nested loop 410 k loops, hash + sort spills; rewrite predicate / expression index; `ANALYZE`; `work_mem` only per session and last |
| 4 | Single: PG | "Page 4 000 of the AWB event list takes 6 s (OFFSET/LIMIT)" | Yes | Keyset pagination with `(event_ts, event_id)` row comparison, matching index, trade-off (no page jump) |
| 5 | Single: MS-SQL | "We get deadlocks between the ULD scan insert and the status update job" | Yes | Asks for / reads `xml_deadlock_report` from `system_health`; access order, index for UPDATE predicate, shorter transactions, RCSI trade-offs, retry on 1205; no `NOLOCK` |
| 6 | Single: Mongo | "`find({station, status}).sort({createdAt:-1})` is slow" + explain | Yes | Reads `COLLSCAN`, docs examined vs returned, in-memory `SORT`; ESR compound index with RAM/write cost; `$match` first in pipelines |
| 7 | Single: Redis | "Redis latency spikes every few minutes on the flight cache" | Yes | `SLOWLOG`, `--bigkeys`, `--hotkeys`, `KEYS` → `SCAN`, `UNLINK`, TTL jitter; fork/persistence check |
| 8 | Single: DynamoDB/Cosmos | "Cosmos DB 429s while total RU is only 30%" | Yes | Hot logical partition; normalized RU per partition key range; higher-cardinality / synthetic / hierarchical key; point reads |
| 9 | Multi | "Nightly purge of old AWB events blocks the API and the report query also got slow" | Yes | Batch DELETE (marked Destructive, confirmation) or partition drop; blocking diagnosis; separate plan analysis for the report; before/after for both |
| 10 | Multi | "Is our index strategy OK?" + list of 14 indexes on `awb_event` + missing-index DMV output | Yes | Usage vs `user_updates`; overlapping/duplicate indexes; DMV rows treated as suggestions; each proposed change with served query + write cost; no blanket "add all" |
| 11 | Edge: no plan | "Make this query faster" + SQL only | Yes | Engine inferred and stated; `scripts/sql_lint.py` run; SARGable rewrite offered as "expected, verify"; exact command to capture actual plan; no invented timings |
| 12 | Edge: huge plan | 40 000-line `.sqlplan` from a 30-statement proc | Yes | Runs analyzer with `--top`; focuses on the costliest statements/nodes; does not paste the plan back; asks which statement is the slow one if unclear |
| 13 | Edge: unknown engine | "Our DB is slow, fix it" (no engine, no query) | Yes | Asks for engine/version and the top queries; gives per-engine commands (Query Store, `pg_stat_statements`, profiler); no hardware blame |
| 14 | Edge: dangerous request | "Just run DBCC FREEPROCCACHE and rebuild all indexes on prod" | Yes | Refuses to run blind; explains instance-wide impact; targeted alternative (single plan evict, `UPDATE STATISTICS`); asks for confirmation |
| 15 | Edge: ORM N+1 | "After the release pg_stat_statements shows 2 M calls of the same SELECT" | Yes | Identifies N+1 from `calls` / `rows_per_call`; set-based query (`= ANY($1)`); hands app change to backend owners |
| 16 | Near-miss | "Design a schema for bookings and allotments" | **No** | Route to database-engineering |
| 17 | Near-miss | "Refactor this messy stored procedure for readability" | **No** | Route to refactoring |
| 18 | Near-miss | "Speed up this C# loop that builds the manifest" | **No** | Route to code-performance |
| 19 | Near-miss | "Write a query for the latest status of each AWB" | **No** | Route to database-engineering (writing, not tuning) |
| 20 | Consistency | Run #2 three times | Yes | Same root cause, same ranked fix order, same report sections 3/3 |
