# SQL Refactoring (T-SQL and PL/pgSQL)

Goal: same result sets, same side effects, same errors, less and clearer code. Tuning for speed
belongs to the sql-performance-tuning skill; schema changes to database-engineering.

## Safety net: result-equivalence check
Run old and new side by side on the **same data** (a restored copy or a transaction you roll back).
Rename the old object to `_old` (or deploy the new one as `_new`) so both exist at once.

**Read-only query / function / proc that returns rows (T-SQL)**
```sql
CREATE TABLE #old (AwbNo VARCHAR(12), DwellHours DECIMAL(9,1), Band VARCHAR(5));
CREATE TABLE #new (AwbNo VARCHAR(12), DwellHours DECIMAL(9,1), Band VARCHAR(5));
INSERT #old EXEC dbo.usp_DwellReport_old @Station = 'BOM';
INSERT #new EXEC dbo.usp_DwellReport     @Station = 'BOM';

SELECT 'only_old' AS side, * FROM (SELECT * FROM #old EXCEPT SELECT * FROM #new) d
UNION ALL
SELECT 'only_new', * FROM (SELECT * FROM #new EXCEPT SELECT * FROM #old) d;   -- expect 0 rows

SELECT (SELECT COUNT(*) FROM #old) AS rows_old, (SELECT COUNT(*) FROM #new) AS rows_new,
       (SELECT CHECKSUM_AGG(CHECKSUM(*)) FROM #old) AS chk_old,
       (SELECT CHECKSUM_AGG(CHECKSUM(*)) FROM #new) AS chk_new;              -- expect equal pairs
```
`EXCEPT` removes duplicates, so the row counts catch "same rows, different multiplicity".

**PostgreSQL** (`EXCEPT ALL` keeps duplicates, so it checks multiplicity directly)
```sql
SELECT 'only_old' AS side, * FROM (SELECT * FROM cargo.dwell_report_old('BOM', now())
                                   EXCEPT ALL SELECT * FROM cargo.dwell_report('BOM', now())) d
UNION ALL
SELECT 'only_new', * FROM (SELECT * FROM cargo.dwell_report('BOM', now())
                           EXCEPT ALL SELECT * FROM cargo.dwell_report_old('BOM', now())) d;
```
Pass a fixed timestamp instead of `now()` if the two calls could straddle a boundary.

**Procedure that writes (UPDATE/INSERT/DELETE)**: run old, capture, roll back; run new, capture,
roll back; compare. Capture into **table variables**: they keep their rows after `ROLLBACK`
(temp-table inserts are rolled back with the transaction).
```sql
DECLARE @after_old TABLE (FlightId INT, TotalKg DECIMAL(12,2), TotalPcs INT, LoadStatus CHAR(3));
DECLARE @after_new TABLE (FlightId INT, TotalKg DECIMAL(12,2), TotalPcs INT, LoadStatus CHAR(3));

BEGIN TRAN;
EXEC dbo.usp_RecalcFlightLoad_old @FlightId = 42;
INSERT @after_old SELECT FlightId, TotalKg, TotalPcs, LoadStatus FROM dbo.Flight WHERE FlightId = 42;
ROLLBACK;

BEGIN TRAN;
EXEC dbo.usp_RecalcFlightLoad @FlightId = 42;
INSERT @after_new SELECT FlightId, TotalKg, TotalPcs, LoadStatus FROM dbo.Flight WHERE FlightId = 42;
ROLLBACK;

SELECT 'only_old' AS side, * FROM (SELECT * FROM @after_old EXCEPT SELECT * FROM @after_new) d
UNION ALL
SELECT 'only_new', * FROM (SELECT * FROM @after_new EXCEPT SELECT * FROM @after_old) d;  -- expect 0 rows
```
Widen the `WHERE` (or loop over a list of ids) to cover rows the proc should *not* touch too.
Repeat for edge rows: no child rows, NULL columns, cancelled status, boundary values, error path
(missing key → same error number/message).

## Refactorings

| Smell | Refactoring | Behaviour trap |
|---|---|---|
| Cursor / `FOR rec IN` loop doing sums or updates | Set-based `UPDATE ... FROM`, `SUM`, `INSERT ... SELECT` | `SUM` of no rows is `NULL`: wrap in `COALESCE(...,0)`; `<>` drops NULLs like the loop's `IF` did; row-by-row side effects (triggers per row, `@@ROWCOUNT` checks) change |
| Same subquery 2+ times | CTE or `CROSS APPLY` / `LATERAL` / join | Scalar subquery errors on > 1 row; a join silently multiplies rows: check the key is unique |
| Arrow-shaped `IF ... BEGIN ... END` | Guard clause + `RETURN` (T-SQL) / `RETURN;` (PL/pgSQL) | Make sure nothing after the block still ran on the error path |
| `IF/ELSIF` ladder assigning a value | `CASE` expression | `CASE` returns `NULL` when nothing matches and no `ELSE` |
| Magic codes `'CXL'`, `0.9` | Named variable / lookup table / `CONST`-like CTE | Keep data types identical (`CHAR(3)` vs `VARCHAR`) |
| God-procedure (validation + calc + write + notify) | Split into child procs/functions, keep the old name as orchestrator | Transaction scope must stay the same; nested `BEGIN TRAN` counts in T-SQL |
| Copy-pasted procs differing by one column | One proc with a parameter, or a view | Parameter sniffing is a perf concern: hand to sql-performance-tuning if plans change |
| Dynamic SQL built by concatenation | `sp_executesql` with parameters / `format('%I', ...)` + `USING` | That is a security fix: list it separately, hand to security-review-fix |
| Inconsistent style | Keywords upper, one clause per line, table aliases, schema-qualified names, `;` terminators | Follow the repo's existing style if it has one |

## Transaction and error hygiene (T-SQL)
```sql
-- before: partial updates survive an error
UPDATE dbo.Booking SET StatusCode = 'CXL' WHERE BookingId = @Id;
INSERT dbo.BookingAudit (BookingId, Action) VALUES (@Id, 'CXL');

-- after
SET XACT_ABORT ON;
BEGIN TRY
    BEGIN TRAN;
    UPDATE dbo.Booking SET StatusCode = 'CXL' WHERE BookingId = @Id;
    INSERT dbo.BookingAudit (BookingId, Action) VALUES (@Id, 'CXL');
    COMMIT;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK;
    THROW;
END CATCH;
```
Strictly this changes behaviour on failure (all-or-nothing instead of partial). It is usually the
intent, but list it under "Behaviour changes (approved?)" in the report rather than hiding it.

PL/pgSQL: a function already runs in the caller's transaction; don't add `COMMIT` inside a
function. Use `EXCEPTION WHEN ... THEN` only where the old code handled the error; a blanket
handler that swallows errors is a behaviour change.

## Worked samples
- `templates/samples/tsql_before.sql` → `tsql_after.sql`: cursor → `SUM`, duplicated subquery → join, guard clause.
- `templates/samples/plpgsql_before.sql` → `plpgsql_after.sql`: `FOR` loop + `RETURN NEXT` → `RETURN QUERY` + CTE + `CASE`.
  Verified on PostgreSQL 16 with 20,003 rows: identical counts, 0 rows in `EXCEPT ALL` both ways.

## Formatting defaults (when the repo has none)
- Keywords UPPER in T-SQL, lower in PostgreSQL if the repo is lower-case; be consistent in a file.
- One column per line in long `SELECT` lists; `JOIN ... ON` on its own line; aliases short but meaningful (`b` for Booking, `f` for Flight).
- Schema-qualify every object (`dbo.`, `cargo.`); terminate statements with `;`.
- `CREATE OR ALTER` (SQL Server 2016 SP1+) / `CREATE OR REPLACE` keeps permissions on redeploy; `DROP` + `CREATE` loses grants.
