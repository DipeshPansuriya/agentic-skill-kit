# Example (FAKE DATA): Release 5.2.0 (2026-10-01)

## A. Client-facing
**Highlights:** Collect import cargo faster with online delivery orders.

### Action required
- API users: switch from `/v1/awb/status` to `/v2/shipments/status` by 2026-11-30. After that date the old endpoint stops responding.

### New
- You can now receive your delivery order online as soon as charges are paid.

### Improved
- AWB search results now load up to 3x faster.

### Fixed
- Air waybill data now reaches airlines reliably after brief network interruptions.

### Known issues
- ULD screen may show weight with 2 decimals for older records. Workaround: refresh the record.

## B. Internal (excerpt)
### Breaking / Action required
| Ticket | Change | Who is affected | Migration | Rollback |
|---|---|---|---|---|
| CCS-1420 | `/v1/awb/status` renamed to `/v2/shipments/status` | API partners (4) | v1 alias kept until 2026-11-30 | Re-enable v1 route flag `api.v1.status` |

### New / Improved / Fixed
| Category | Ticket | Component | Summary |
|---|---|---|---|
| New | CCS-1412 | edo | Issue e-DO after payment |
| Improved | CCS-1405 | search | Index on awb_no |
| Fixed | CCS-1398 | fwb | Retry FWB send on TLS handshake failure |
