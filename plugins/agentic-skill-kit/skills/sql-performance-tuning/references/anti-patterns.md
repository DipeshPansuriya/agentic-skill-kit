# Query Anti-Patterns (before / after)

Every rewrite must return the same rows as the original (check NULLs, duplicates, ordering). Measure both versions with the same parameters.

| # | Anti-pattern | Cost | Engines |
|---|---|---|---|
| 1 | `SELECT *` | Blocks covering indexes, extra IO/network, breaks on schema change | All |
| 2 | Non-SARGable predicates | Scan instead of seek | All |
| 3 | `OR` across different columns | Scan or poor plan | All |
| 4 | `NOT IN` with nullable subquery | **Wrong results** + anti-join issues | All |
| 5 | Scalar UDF in `WHERE` / `SELECT` | Row-by-row execution, serial plan | SQL Server (pre-inlining), PG (non-inlinable plpgsql) |
| 6 | Cursors / RBAR loops | N round trips, N log flushes | All |
| 7 | `OFFSET` deep paging | Reads offset + page rows | All |
| 8 | `DISTINCT` to hide duplicate joins | Sort/hash over inflated rows; hides a logic bug | All |
| 9 | Implicit conversions | Scan, bad estimates | SQL Server mainly; PG on mismatched types |
| 10 | CTE assumptions | Re-evaluation or optimisation fence | Both, differently |

## 1. SELECT *
```sql
-- Before
SELECT * FROM awb_event WHERE awb_no = @awb;
-- After: only what the caller uses; lets (awb_no, event_ts) INCLUDE (status_code, station) cover it
SELECT awb_no, event_ts, status_code, station FROM awb_event WHERE awb_no = @awb;
```

## 2. Non-SARGable predicates
```sql
-- Before (function on column)
WHERE YEAR(event_ts) = 2026 AND MONTH(event_ts) = 9
WHERE CAST(awb_no AS bigint) = 17612345675
WHERE ISNULL(status_code, 'NEW') = 'NEW'
WHERE DATEADD(day, 7, created_at) > GETDATE()
-- After (bare column compared to a computed value)
WHERE event_ts >= '2026-09-01' AND event_ts < '2026-10-01'
WHERE awb_no = '17612345675'                         -- compare in the column's type
WHERE (status_code = 'NEW' OR status_code IS NULL)
WHERE created_at > DATEADD(day, -7, GETDATE())
```
If the function is unavoidable: PG expression index (`ON shipment (lower(shipper_ref))`); SQL Server persisted computed column + index.

## 3. OR across columns
```sql
-- Before: one index cannot serve both branches → scan
SELECT shipment_id FROM shipment WHERE shipper_id = @id OR consignee_id = @id;
-- After: each branch seeks its own index; UNION removes rows matching both
SELECT shipment_id FROM shipment WHERE shipper_id   = @id
UNION
SELECT shipment_id FROM shipment WHERE consignee_id = @id;
```
Catch-all search (`WHERE (@awb IS NULL OR awb_no = @awb) AND (@stn IS NULL OR station = @stn)`): SQL Server `OPTION (RECOMPILE)` for infrequent use, or build parameterised dynamic SQL with only the supplied predicates (`sp_executesql`). PG can use BitmapOr for same-table ORs; still verify in the plan.

## 4. NOT IN with NULLs
```sql
-- Before: returns 0 rows if any hold.awb_no IS NULL; also blocks efficient anti-join
SELECT a.awb_no FROM awb a WHERE a.awb_no NOT IN (SELECT h.awb_no FROM hold h);
-- After: correct with NULLs; plans as anti semi-join
SELECT a.awb_no FROM awb a
WHERE NOT EXISTS (SELECT 1 FROM hold h WHERE h.awb_no = a.awb_no);
```

## 5. Scalar UDF in WHERE
```sql
-- Before (SQL Server): function runs per row, forces serial plan if not inlinable
SELECT awb_no FROM dbo.shipment WHERE dbo.fn_chargeable_kg(gross_kg, volume_m3) > 1000;
-- After: inline the expression (IATA volumetric 1 m3 = 167 kg) or use an inline TVF
SELECT awb_no FROM dbo.shipment
WHERE CASE WHEN volume_m3 * 167 > gross_kg THEN volume_m3 * 167 ELSE gross_kg END > 1000;
```
2019+ may inline automatically (`sys.sql_modules.is_inlineable = 1`); verify in the plan. PG: prefer `LANGUAGE sql IMMUTABLE` functions (inlinable) over plpgsql.

## 6. Cursors / RBAR
```sql
-- Before: one UPDATE per row, one log flush per row
DECLARE c CURSOR FOR SELECT awb_no FROM dbo.staging_status;
-- ... FETCH NEXT ... UPDATE dbo.shipment SET status_code = @s WHERE awb_no = @awb ...
-- After: one set-based statement (batch if millions of rows)
UPDATE s SET s.status_code = st.status_code, s.updated_at = SYSUTCDATETIME()
FROM dbo.shipment s
JOIN dbo.staging_status st ON st.awb_no = s.awb_no
WHERE s.status_code <> st.status_code;          -- skip no-op writes
```

## 7. OFFSET deep paging
```sql
-- Before: page 5 000 reads 100 000+ rows then discards them
SELECT awb_no, event_ts, status_code FROM awb_event
ORDER BY event_ts DESC, event_id DESC
OFFSET 100000 ROWS FETCH NEXT 20 ROWS ONLY;
-- After: keyset (seek) pagination; client sends last row's (event_ts, event_id)
SELECT awb_no, event_ts, status_code, event_id FROM awb_event
WHERE (event_ts < @last_ts) OR (event_ts = @last_ts AND event_id < @last_id)
ORDER BY event_ts DESC, event_id DESC
FETCH FIRST 20 ROWS ONLY;                     -- PG syntax; SQL Server: SELECT TOP (20) ... or OFFSET 0 ROWS FETCH NEXT 20 ROWS ONLY
-- PG shorthand: WHERE (event_ts, event_id) < ($1, $2)   (row comparison, index-friendly)
-- Index: (event_ts DESC, event_id DESC) INCLUDE (awb_no, status_code)
```
Trade-off: no "jump to page N"; stable under concurrent inserts.

## 8. DISTINCT hiding duplicate joins
```sql
-- Before: join to events multiplies rows, DISTINCT removes them after the fact
SELECT DISTINCT s.awb_no, s.origin, s.dest
FROM shipment s JOIN awb_event e ON e.awb_no = s.awb_no
WHERE e.status_code = 'DEP';
-- After: semi-join expresses "has at least one DEP event"
SELECT s.awb_no, s.origin, s.dest
FROM shipment s
WHERE EXISTS (SELECT 1 FROM awb_event e WHERE e.awb_no = s.awb_no AND e.status_code = 'DEP');
```

## 9. Implicit conversions
```sql
-- Before (SQL Server): awb_no is VARCHAR(12); .NET sends NVARCHAR(4000) → CONVERT_IMPLICIT on the column
EXEC sp_executesql N'SELECT status_code FROM dbo.awb_event WHERE awb_no = @awb',
                   N'@awb nvarchar(4000)', @awb = N'17612345675';
-- After: parameter typed like the column
EXEC sp_executesql N'SELECT status_code FROM dbo.awb_event WHERE awb_no = @awb',
                   N'@awb varchar(12)', @awb = '17612345675';
```
```sql
-- SQL Server: awb_no VARCHAR compared to an INT literal → column converted to INT (precedence), scan + conversion errors on 'ABC'
WHERE awb_no = 17612345675
WHERE awb_no = '17612345675'      -- compare in the column's type
-- PG: text = bigint raises "operator does not exist"; a cast on the column (awb_no::bigint = $1) blocks the index
```
Also: joins between columns of different types (`INT` vs `BIGINT`, `VARCHAR` vs `NVARCHAR`) → align the schema.

## 10. CTE assumptions
| Belief | Reality |
|---|---|
| "A CTE is computed once" (SQL Server) | CTEs are inlined; referenced twice = evaluated twice. Materialise into `#temp` (gets statistics) when reused and expensive |
| "A CTE is an optimisation fence" (PG) | Only before PG12. PG12+ inlines non-recursive, side-effect-free CTEs referenced once; `AS MATERIALIZED` / `NOT MATERIALIZED` to choose |
| "CTEs make it faster" | They are for readability; plan is what counts |
```sql
-- PG12+: force single evaluation of an expensive CTE used twice
WITH last_evt AS MATERIALIZED (
  SELECT DISTINCT ON (awb_no) awb_no, status_code, event_ts
  FROM awb_event WHERE event_ts >= now() - interval '1 day'
  ORDER BY awb_no, event_ts DESC
)
SELECT ... FROM last_evt ... JOIN last_evt ...;
```
