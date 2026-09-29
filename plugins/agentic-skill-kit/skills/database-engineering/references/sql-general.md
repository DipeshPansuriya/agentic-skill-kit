# SQL: Writing Correct, Set-Based Queries

ANSI SQL first; engine notes marked **PG** (PostgreSQL) and **MS** (SQL Server).

## Query writing checklist
- Explicit column list; table aliases on every column in multi-table queries.
- ANSI `JOIN ... ON`, never comma joins (easy to lose a predicate → cartesian product).
- Filter early, but put **outer-join** filters in the `ON` clause, not `WHERE` (a `WHERE` on the right table turns a `LEFT JOIN` into an inner join).
- Parameters, not literals concatenated from input.
- Deterministic `ORDER BY` for paging (add a unique tie-breaker, e.g. `ORDER BY event_ts, event_id`).
- Paging on big tables: keyset (`WHERE (event_ts, event_id) > (@ts, @id)`) beats `OFFSET n` (which reads and discards n rows). **MS** has no row-value comparison: write `event_ts > @ts OR (event_ts = @ts AND event_id > @id)`.

## NULL traps
| Trap | Why | Fix |
|---|---|---|
| `x NOT IN (SELECT y ...)` where `y` can be NULL | `x <> NULL` is UNKNOWN → returns **zero rows** | `NOT EXISTS (SELECT 1 ... WHERE y = x)` |
| `WHERE col <> 'X'` | Excludes rows where `col IS NULL` | `WHERE col <> 'X' OR col IS NULL` (**PG**: `col IS DISTINCT FROM 'X'`; **MS 2022**: `IS DISTINCT FROM` too) |
| `COUNT(col)` vs `COUNT(*)` | `COUNT(col)` skips NULLs | Pick deliberately |
| `SUM/AVG` on all-NULL group | Returns NULL, not 0 | `COALESCE(SUM(x), 0)` |
| `col = NULL` | Never true | `col IS NULL` |
| Concatenation with NULL | `'A' \|\| NULL` = NULL (**MS** `+` too) | `CONCAT()` treats NULL as '' |
| Unique index + NULLs | **PG**: multiple NULLs allowed (unless `NULLS NOT DISTINCT`, PG15+); **MS**: only one NULL | Filtered unique index in MS: `WHERE col IS NOT NULL` |

## CTEs
- Use for readability and recursion (`WITH RECURSIVE` in **PG**; plain `WITH` in **MS**).
- **PG 12+** inlines non-recursive CTEs referenced once; force materialisation with `AS MATERIALIZED` when reuse is expensive.
- **MS** never materialises CTEs: a CTE referenced twice runs twice. Use a `#temp` table if it is expensive.
- Recursive CTEs need a termination guard (depth column; **MS** `OPTION (MAXRECURSION n)`, default 100).

## Window functions
```sql
-- Latest status per AWB (the "top-1 per group" pattern)
SELECT awb_no, status_code, event_ts
FROM (
  SELECT awb_no, status_code, event_ts,
         ROW_NUMBER() OVER (PARTITION BY awb_no ORDER BY event_ts DESC, event_id DESC) AS rn
  FROM awb_event
  WHERE event_ts >= :since
) t
WHERE rn = 1;
```
- `ROW_NUMBER` (unique), `RANK` (gaps on ties), `DENSE_RANK` (no gaps).
- `LAG/LEAD` for time between events (dwell time): `event_ts - LAG(event_ts) OVER (PARTITION BY awb_no ORDER BY event_ts)`.
- Running totals: specify the frame: `SUM(pcs) OVER (PARTITION BY flight_id ORDER BY event_ts ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)`. Default frame with `ORDER BY` is `RANGE`, which lumps ties together and is slower in **MS**.
- Supporting index: `(partition cols, order cols) INCLUDE (selected cols)`.
- **PG** alternative for top-1: `SELECT DISTINCT ON (awb_no) ... ORDER BY awb_no, event_ts DESC`.
- For "latest per group" across very many groups with few rows needed, `LATERAL` (**PG**) / `CROSS APPLY` (**MS**) with `LIMIT 1`/`TOP 1` on an index can beat a full window scan.

## Set-based vs row-by-row
- Replace cursors/loops with one `UPDATE ... FROM` / `MERGE`-style statement or an `INSERT ... SELECT`.
- Scalar functions called per row are a hidden loop (**MS** before 2019 scalar UDF inlining; still check `is_inlineable`).
- Batch huge writes to control locks and log growth:
```sql
-- MS: batch delete of old scan events
DECLARE @n int = 1;
WHILE @n > 0
BEGIN
  DELETE TOP (5000) FROM dbo.uld_scan WHERE scan_ts < @cutoff;
  SET @n = @@ROWCOUNT;
END
```
- **PG** batch: `DELETE FROM uld_scan WHERE ctid = ANY (ARRAY(SELECT ctid FROM uld_scan WHERE scan_ts < $1 LIMIT 5000));`, or better, drop old partitions.

## Upsert
- **PG**: `INSERT ... ON CONFLICT (awb_no) DO UPDATE SET status = EXCLUDED.status` (needs a unique index/constraint). PG15+ also has `MERGE`.
- **MS**: `MERGE` has known concurrency and bug history; prefer `UPDATE ... ; IF @@ROWCOUNT = 0 INSERT ...` inside a transaction with `WITH (UPDLOCK, SERIALIZABLE)` on the update.

## Aggregation
- Conditional aggregates: `COUNT(*) FILTER (WHERE status='DLV')` (**PG**) or `SUM(CASE WHEN status='DLV' THEN 1 ELSE 0 END)` (portable).
- `GROUP BY` every non-aggregated column (PG allows functional dependency on PK).
- `HAVING` filters groups; row filters belong in `WHERE`.

## Dates and time zones
- Store UTC (`timestamptz` in **PG**, `datetime2`/`datetimeoffset` in **MS**); convert at the edge. Flight local times: store the airport's IANA zone separately.
- Range predicates: `event_ts >= @d AND event_ts < @d + 1 day`; never `BETWEEN` for timestamps, never `CAST(event_ts AS date) = @d` on big tables in older engines.
