# Schema Design and Zero-Downtime Migrations

## Start from access patterns
Before drawing tables, list: top 5–10 queries, write rate per table, retention, and who reports on it. Model entities to 3NF, then denormalise only where a measured query needs it.

## Normalisation vs denormalisation
| Choose | When | Cost |
|---|---|---|
| Normalised (3NF) | OLTP writes, integrity matters (bookings, rates, customers) | More joins |
| Denormalised copy / summary table | Hot read path, dashboards, search | Sync logic, staleness, update anomalies |
| Materialised view (PG `REFRESH MATERIALIZED VIEW CONCURRENTLY`, needs a unique index) / indexed view (MS) | Aggregates read far more than written | Refresh cost / write overhead |
| Star schema in a warehouse | Analytics over years of events | Separate ETL/ELT |

Denormalise by **copying**, not by giving up the source of truth.

## Keys
- Surrogate PK: `bigint` identity (`GENERATED ALWAYS AS IDENTITY` in PG; `BIGINT IDENTITY` in MS). Use `int` only for small reference tables; event tables outgrow `int` (2.1 bn).
- UUIDs: when IDs are generated outside the DB or merged across systems; prefer time-ordered **UUIDv7** (PG18 has `uuidv7()`; generate in the app otherwise) to avoid random-insert index bloat.
- Always also enforce the **natural key** with a unique constraint (e.g. `UNIQUE (awb_prefix, awb_serial)`; `UNIQUE (carrier_code, flight_no, flight_date)`).
- Foreign keys: declare them; index the FK column on the child table when you delete/update parents or join on it.
- Data types: exact numerics for money/weight (`numeric(12,3)` / `decimal`), never float; `timestamptz` / `datetime2`/`datetimeoffset`; codes as `char(3)` (IATA airport) with `CHECK` constraints.

## Naming conventions
- `snake_case` (PG, avoids quoting) or the team's existing convention (MS shops often `PascalCase`); be consistent.
- Singular or plural tables: pick one and keep it.
- `<table>_id` for PK/FK columns; booleans `is_`/`has_`; timestamps `_at`; dates `_date`.
- Name constraints and indexes explicitly: `pk_shipment`, `fk_awb_event_shipment`, `ix_awb_event_awb_no_event_ts`, `uq_shipment_awb`, `ck_shipment_weight_pos`.
- No reserved words (`user`, `order`, `status` is fine), no spaces, no type prefixes (`tbl_`).

## Audit columns
```sql
created_at  timestamptz NOT NULL DEFAULT now(),
created_by  text        NOT NULL,
updated_at  timestamptz NOT NULL DEFAULT now(),
updated_by  text        NOT NULL,
row_version bigint      NOT NULL DEFAULT 1   -- optimistic concurrency (MS: rowversion type)
```
- Set `updated_*` in the app or a trigger, consistently.
- For full history use a separate audit/history table (MS **temporal tables** `SYSTEM_VERSIONING = ON`; PG trigger-based history or CDC), not extra columns.
- Regulatory data (customs, dangerous goods): keep immutable event rows; never update in place.

## Soft delete trade-offs
| Soft delete (`deleted_at`) | Hard delete (+ archive/history table) |
|---|---|
| Easy undo, keeps references | Simple queries, real uniqueness |
| Every query must filter `deleted_at IS NULL` (views/RLS help) | Needs archive or history for audit |
| Unique constraints must become partial/filtered: `UNIQUE (awb_no) WHERE deleted_at IS NULL` | FKs need `ON DELETE` strategy |
| Table and indexes grow; GDPR erasure still needs hard delete | |

Default: hard delete + history/audit table for most entities; soft delete only where users expect "restore".

## Zero-downtime migrations: expand / contract
Old and new app versions run side by side during a deploy; every step must work with both.

1. **Expand**: add new things, additive only: new nullable column / new table / new index (`CONCURRENTLY` / `ONLINE = ON`).
2. **Dual write**: app writes old and new shape (or a trigger does).
3. **Backfill** in batches (e.g. 5 000 rows, short transactions, sleep between batches; resumable by key range); monitor replication lag.
4. **Switch reads** to the new shape (feature flag).
5. **Enforce**: add `NOT NULL` / FK / CHECK using `NOT VALID` + `VALIDATE` (PG) or `WITH NOCHECK` then `WITH CHECK CHECK CONSTRAINT` (MS, the latter scans; schedule off-peak).
6. **Contract**: stop writing the old shape, deploy, then drop old column/table in a later release.

Example: rename `shipper_nm` → `shipper_name`: never `RENAME` in one step with running apps. Add `shipper_name`, dual-write, backfill, switch reads, drop `shipper_nm` later.

Migration hygiene:
- One versioned, reviewed script per change (Flyway, Liquibase, EF Core migrations, DbUp, sqitch); never edit an applied migration.
- Every migration has a tested down/rollback path or an explicit "forward-fix only" note.
- PG: `SET lock_timeout` and `statement_timeout` in migration sessions; MS: `SET LOCK_TIMEOUT` and `WAIT_AT_LOW_PRIORITY` for online index ops.
- Check which operations rewrite/lock the table (see `postgresql.md` Locking; MS: most column type changes are size-of-data; adding a `NOT NULL` column with a runtime-constant default is metadata-only on Enterprise/Azure SQL).

## Data fix template
```sql
-- Engine: PostgreSQL 16. Ticket: <id>. Expected rows: 42.
BEGIN;
SELECT count(*) FROM shipment WHERE status = 'RCS' AND flight_id IS NULL AND created_at < '2026-09-01';  -- before: expect 42
UPDATE shipment SET status = 'NEW', updated_at = now(), updated_by = 'fix-ticket'
WHERE status = 'RCS' AND flight_id IS NULL AND created_at < '2026-09-01';
-- verify: must return 0
SELECT count(*) FROM shipment WHERE status = 'RCS' AND flight_id IS NULL AND created_at < '2026-09-01';
-- If counts match: COMMIT;  otherwise: ROLLBACK;
-- Rollback after commit: restore from the backup table created by
--   CREATE TABLE fix_ticket_backup AS SELECT * FROM shipment WHERE ...;  (run before BEGIN)
```
(Replace the ticket id placeholder with the real ticket.)
