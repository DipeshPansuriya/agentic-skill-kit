# Example (FAKE DATA): INC-0000 FWB messages to airline not delivered

**Severity:** SEV2 (criterion: "FWB/FFM messages not reaching an airline") · **Status:** Resolved · **Date:** 2026-09-21 · **Audience:** Internal

## 1. Summary
FWB messages from the cargo community system to Airline XX were not delivered for 75 minutes. 3 forwarders saw stale AWB status; 212 FWBs queued. Root cause: the EDI gateway TLS certificate expired and no expiry alert existed. Certificate rotated, queue drained, all messages delivered by 15:35 IST.

## 2. Impact
| Dimension | Value |
|---|---|
| Customers affected | 3 forwarders, 1 airline |
| Messages affected | 212 FWB queued, 0 lost |
| SLA breached | Y: message delivery ≤ 15 min |
| Duration (TTR) | 1h 15m |
| TTD | 0h 20m |
| Financial / regulatory exposure | TBD |

## 3. Timeline (from `scripts/timeline.py`)
| # | UTC | IST | Event | Marker |
|---|---|---|---|---|
| 1 | 2026-09-21 08:50 | 2026-09-21 14:20 | Impact start: first EDI send failure in logs | START |
| 2 | 2026-09-21 09:10 | 2026-09-21 14:40 | Ops detected FWB messages stuck in queue | DETECTED |
| 3 | 2026-09-21 09:30 | 2026-09-21 15:00 | Forwarder reports AWB 000-00000000 status stale | |
| 4 | 2026-09-21 09:50 | 2026-09-21 15:20 | Expired TLS cert identified; cert rotated | |
| 5 | 2026-09-21 10:05 | 2026-09-21 15:35 | Queue drained, service resolved | RESOLVED |

## 5. Root cause (excerpt)
| Level | Answer | Evidence |
|---|---|---|
| Symptom | Forwarders saw stale AWB status | Customer email 15:00 IST |
| Why 1 | FWBs not delivered to airline | Queue depth 212 |
| Why 2 | TLS handshake to airline endpoint failed | Gateway log |
| Why 3 | Gateway certificate expired | Cert expiry 2026-09-21 08:49 UTC |
| Why 4 | Renewal was a manual calendar task | Runbook |
| Root cause | No automated cert-expiry monitoring or renewal | Confirmed |

## 7. Actions (excerpt)
| # | Action | Type | Owner | Due | Ticket | Status |
|---|---|---|---|---|---|---|
| 1 | Rotate cert and verify all partner endpoints | Corrective | Infra on-call | 2026-09-21 | TBD | Done |
| 2 | Alert at 30/7/1 days before any cert expiry | Preventive | Platform lead | 2026-10-05 | TBD | Open |
| 3 | Alert when FWB queue depth > 50 for 5 min | Preventive | TBD | TBD | TBD | Open |
