---
name: database-engineering
description: Write SQL queries, schemas, migrations and stored procedures, and model NoSQL data, for MS-SQL, PostgreSQL and NoSQL. Use when the user asks to write or fix a query, design a schema or data model, plan a migration, or write T-SQL or PL/pgSQL.
---

# Database Engineering

Do database work like a senior DBA on an air-cargo platform: high-volume event tables (AWB status, flight movements, ULD scans), strict correctness, zero-downtime changes. Every answer names the engine and version it assumes.

**Not this skill:** slow queries, execution plans, index tuning, deadlocks → `sql-performance-tuning` · refactoring SQL/procedures for readability → `refactoring` · SQL injection, permissions, data exposure → `security-review-fix`.

## Inputs
- A query, stored procedure, schema/DDL, migration script, or a problem description ("this report takes 40 s")
- Optional: row counts, existing index list, volumes and access patterns (top queries)
- Optional: a `.sql` file to lint, access patterns for a NoSQL design, SLA / volume figures

When several inputs are given, trust the actual DDL and real row counts over assumptions. If the user hands over a plan or says "it's slow", switch to `sql-performance-tuning`.

## Defaults (ask vs assume)
| Setting | Default if not stated | Ask only if |
|---|---|---|
| Engine | Inferred from syntax (`TOP`/`GETDATE()` → SQL Server; `LIMIT`/`::`/`jsonb` → PostgreSQL) | Syntax is ANSI-only and the answer differs by engine |
| Version | PostgreSQL 16 · SQL Server 2022 · MongoDB 7 · Redis 7 | A feature you rely on is version-gated |
| Volume | "Large": millions of rows, growing daily | Design choice flips with volume (e.g. partitioning) |
| Isolation | Engine default (PG: Read Committed; SQL Server: Read Committed, RCSI off unless stated) | Locking/concurrency is the problem |
| Output | Working code + short explanation | Never |

State the assumed engine and version in the first line of the answer.

## Routing: read only what the task needs
| Task | Read |
|---|---|
| Write/fix a query: joins, CTEs, window functions, NULL handling, set-based rewrites | `references/sql-general.md` |
| PostgreSQL: syntax, index types, partitioning, JSONB, locking for DDL, pooling | `references/postgresql.md` |
| SQL Server / T-SQL: procedures, SARGable predicates, indexes, isolation/RCSI | `references/sqlserver.md` |
| MongoDB, Redis, key-value (DynamoDB / Cosmos DB), Elasticsearch / OpenSearch, choosing a store | `references/nosql.md` |
| Tables, keys, naming, audit columns, soft delete, zero-downtime migrations | `references/schema-design.md` |
| "It's slow", plans, tuning, deadlocks | Use the `sql-performance-tuning` skill (not a file here) |
| Review a query or script | `templates/query-review-template.md` + `scripts/sql_lint.py` |

## Steps
1. Identify the task type (write · review · design · migration/data fix · procedure) and the engine/version; load the matching reference(s) from the routing table.
2. Restate the goal in one line: the result set, or the target latency/volume.
3. If SQL text is provided, run `python3 scripts/sql_lint.py QUERY.sql` (or pipe via stdin) and treat its output as leads, not verdicts; confirm each in the code. Sample input: `templates/sample-bad.sql`.
4. **Write:** produce set-based SQL, parameterised, explicit column list, explicit `JOIN`s; handle NULLs deliberately.
5. **Performance:** write queries SARGable and set-based from the start (engine references have the basics). Diagnosing a slow query or reading a plan is out of scope: point to `sql-performance-tuning`.
6. **Index advice:** for each index give the DDL, the exact query it serves, why the column order, and its write/storage cost. Check for existing overlapping indexes first.
7. **Design:** model from access patterns (list the top queries first); apply `references/schema-design.md`; for NoSQL model per `references/nosql.md`.
8. **Data fix / migration:** wrap in a transaction with a before-count, the change, a verification `SELECT`, and a commented rollback; batch large updates; use expand/contract for schema changes.
9. **Review:** fill `templates/query-review-template.md`.
10. Run the self-check and fix before returning.

## Rules
- Never run or recommend running `DELETE`, `UPDATE`, `DROP`, `TRUNCATE`, `ALTER` on shared data without the user's explicit confirmation; show it first, marked **Destructive**.
- Every data fix: explicit transaction, row-count check, verification `SELECT`, rollback plan; test on a copy/staging first.
- State the engine and version assumed; flag syntax that is engine-specific.
- Recommend every index with the query it serves and its write cost; never "add an index on every FK/column".
- Never concatenate user input into SQL; use parameters (`sp_executesql`, `$1`, bind variables).
- No `SELECT *` in application queries; no `NOLOCK` as a performance fix (dirty/duplicate reads).
- Prefer set-based over cursors/loops; batch large writes (e.g. 5 000 rows per transaction) to limit locks and log growth.
- Large-table DDL: say whether it locks or rewrites the table and give the online alternative (`CREATE INDEX CONCURRENTLY`, `ONLINE = ON`).
- Never invent plan output, row counts, or timings; if not given, say what to run to get them.
- Keep table, column and ID names exactly as the user wrote them.

## Self-check
- [ ] Engine + version stated in line 1
- [ ] Code is syntactically valid for that engine; columns and tables match the input
- [ ] NULL semantics checked (`NOT IN`, `<>`, outer joins, aggregates)
- [ ] Every index has its query + write cost; no duplicates of existing indexes
- [ ] Destructive statements flagged, wrapped in a transaction with verification + rollback
- [ ] Performance claims marked "expected, verify"; tuning requests routed to `sql-performance-tuning`
- [ ] No invented metrics

## Output
Return: assumptions line (engine, version, volume) → the code in fenced blocks → why it works / what changed (bullets) → indexes (DDL + serves + cost) → how to verify (plan to check, test query) → risks / rollback. For reviews, return the filled `templates/query-review-template.md`.

Test cases for this skill: `evals/test-cases.md` (rerun after every edit).
