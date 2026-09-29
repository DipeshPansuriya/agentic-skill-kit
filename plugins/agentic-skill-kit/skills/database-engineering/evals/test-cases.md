# Test Cases: database-engineering

Rerun after every edit. Score each with the 0–5 checklist.

## Quality checklist (1 point each, 0–5)
1. Engine + version stated in line 1; syntax valid for that engine
2. Correct results (NULLs, joins, duplicates) and matches the user's tables/columns
3. Nothing invented (plans, row counts, timings); unknowns say what to run
4. Rules respected (destructive statements flagged + transaction + verify + rollback; indexes with query + write cost)
5. Usable as-is

## Cases
| # | Type | Request | Should trigger? | Expected |
|---|---|---|---|---|
| 1 | Single: SQL writing | "Write a query for the latest status of each AWB from awb_event" | Yes | `ROW_NUMBER() OVER (PARTITION BY awb_no ORDER BY event_ts DESC, ...)` or `DISTINCT ON`; supporting index with cost; engine assumed stated |
| 2 | Single: T-SQL procedure | "Write a stored procedure to upsert flight movements from a staging table" | Yes | `SET NOCOUNT, XACT_ABORT ON`; TRY/CATCH with rollback; set-based `UPDATE` + `INSERT` (or `MERGE` with `HOLDLOCK` caveats); typed parameters |
| 3 | Single: PL/pgSQL | "Write a PostgreSQL function returning open shipments for a station" | Yes | `LANGUAGE sql` or plpgsql with `RETURNS TABLE`; parameterised; SARGable predicate; engine/version stated |
| 4 | Single: SQL Server | "Review: WHERE YEAR(created_at)=2026 AND awb_no = @awb (NVARCHAR)" | Yes | Non-SARGable + implicit conversion flagged; range rewrite; parameter typed VARCHAR (review of written SQL; deep plan diagnosis would go to sql-performance-tuning) |
| 5 | Single: NoSQL | "Design a MongoDB schema for shipments with thousands of tracking events each" | Yes | Separate events collection or bucket pattern (no unbounded array); ESR compound index; access patterns listed first |
| 6 | Single: NoSQL | "Cache flight schedules in Redis" | Yes | Cache-aside, TTL with jitter, eviction policy, invalidation on write, key naming |
| 7 | Single: schema | "Rename shipper_nm to shipper_name on a 200 M row table without downtime" | Yes | Expand/contract steps; batched backfill; no one-step RENAME; lock_timeout |
| 8 | Single: review + lint | "Review this .sql file" + file | Yes | `scripts/sql_lint.py` run; findings confirmed; filled `templates/query-review-template.md` with verdict |
| 9 | Multi | "Design the ULD scan table for PostgreSQL and the matching retention job" | Yes | Monthly range partitions on `scan_ts`, PK includes partition key, `DETACH ... CONCURRENTLY` + `DROP` retention; indexes with cost |
| 10 | Edge: destructive | "Delete all ULD scans older than 2024 in prod now" | Yes | Does not execute; shows batched DELETE marked Destructive, transaction/verification/rollback or partition drop; asks for confirmation |
| 11 | Edge: missing info | "Write a query for AWBs without a DEP event" (no engine) | Yes | Engine inferred or ANSI version given and stated; `NOT EXISTS`; no invented columns |
| 12 | Edge: NULL trap | "Why does NOT IN return no rows?" + query | Yes | Explains NULL in subquery; `NOT EXISTS` rewrite |
| 13 | Edge: DynamoDB | "Pick a partition key for AWB tracking in DynamoDB" | Yes | High-cardinality key (AWB), single-table PK/SK example, GSI for flight lookups, hot-partition warning |
| 14 | Near-miss | "Write a .NET repository class with EF Core for shipments" | **No** | Route to backend-engineering (DB skill only if the SQL/indexing itself is the question) |
| 15 | Near-miss | "Write manual test cases for the shipment search requirement" | **No** | Route to test-cases-from-requirements |
| 16 | Near-miss | "Should we split the booking system into microservices with a database per service?" | **No** | Route to software-architecture |
| 17 | Near-miss | "Here's my EXPLAIN (ANALYZE, BUFFERS) output, why is this 12 s?" | **No** | Route to sql-performance-tuning |
| 18 | Near-miss | "This proc is fast in SSMS but slow from the .NET app" | **No** | Route to sql-performance-tuning (parameter sniffing) |
| 19 | Near-miss | "We keep getting deadlocks on the awb_event table" | **No** | Route to sql-performance-tuning |
| 20 | Near-miss | "Refactor this 600-line stored procedure so it is readable" | **No** | Route to refactoring |
| 21 | Near-miss | "Is this dynamic SQL safe from injection?" | **No** | Route to security-review-fix |
| 22 | Consistency | Run #1 three times | Yes | Same structure 3/3: assumptions line → code → why → index → verify → risks |
