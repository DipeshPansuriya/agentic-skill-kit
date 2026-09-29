# Query Review

**Engine / version assumed:** PostgreSQL 16 | SQL Server 2022 | MongoDB 7 (pick one; say why)  
**Query purpose:** one line: what the result is and who calls it (API, report, batch)  
**Volume assumed:** rows per table, call frequency, latency target  
**Verdict:** Ship | Ship with fixes | Rework

## Lint output
Paste `scripts/sql_lint.py` output; mark each line Confirmed / False positive.

## Findings
| # | Sev | Area | Line | Issue | Why it matters | Fix |
|---|---|---|---|---|---|---|
| 1 | High | Correctness | 12 | `NOT IN (SELECT consignee_id ...)` where column is nullable | Returns 0 rows once any NULL exists | `NOT EXISTS (...)` |
| 2 | Med | Performance | 7 | `WHERE YEAR(created_at) = @y` | Non-SARGable; full scan on 80 M rows | Range: `created_at >= @start AND created_at < @end` |

Sev: **High** = wrong results, data loss, security, outage risk · **Med** = likely slow at real volume, blocking, fragile · **Low** = clarity/maintainability.  
Areas: Correctness · NULL handling · Performance · Concurrency/locking · Security (injection, permissions) · Maintainability.

## Rewritten query
```sql
-- full corrected query, formatted, parameterised
```

## Index recommendations
| DDL | Serves (query / predicate) | Why this column order | Write & storage cost | Replaces / overlaps |
|---|---|---|---|---|
| `CREATE INDEX CONCURRENTLY ix_awb_event_awb_ts ON awb_event (awb_no, event_ts DESC) INCLUDE (status_code);` | Latest status per AWB lookup | Equality on `awb_no`, then sort | +1 index write per insert; ~X GB | None |

## Verification
- Plan to check (what node/row counts should change).
- Test query / expected row count.
- Before/after timing with the slow parameters.

## Risks and rollback
- Locks or rewrites caused by DDL; how to undo (e.g. `DROP INDEX CONCURRENTLY ...`).
- Behaviour changes (row order, NULL handling) callers must know about.

## Not reviewed
Anything out of scope (procedures not provided, ORM-generated SQL, config).
