# Example (FAKE DATA): ST-02 Block e-DO with pending charges

**Requirement:** AC-1 e-DO issued only when all charges paid. AC-2 Refused with reason when any charge pending.

| ID | Title | Req ID | Preconditions | Steps | Test data | Expected result | Priority | Type |
|---|---|---|---|---|---|---|---|---|
| TC-EDO-001 | Issue e-DO when all charges paid | AC-1 | Agent logged in; AWB status ARR | 1. Open e-DO screen 2. Enter AWB 3. Click Issue | AWB 000-00000000, charges 0.00 due | e-DO number generated; status "Issued" | High | Positive |
| TC-EDO-002 | Block e-DO with pending storage | AC-2 | Storage charge unpaid | 1. Open e-DO 2. Enter AWB 3. Click Issue | AWB 000-00000011, storage 1.00 due | Refused: "Charges pending" (assumed message); no e-DO number | High | Negative |
| TC-EDO-003 | Smallest pending amount blocks | AC-2 | Due 0.01 | Same as TC-EDO-002 | Due 0.01 | Refused | Medium | Boundary |
| TC-EDO-004 | Forwarder B cannot issue e-DO for forwarder A's AWB | AC-1 | Logged in as forwarder B | 1. Call issue API with A's AWB | AWB 000-00000022 | 403; no data of A returned | High | Security |

| Req ID | Test case IDs | Covered? |
|---|---|---|
| AC-1 | TC-EDO-001, TC-EDO-004 | Yes |
| AC-2 | TC-EDO-002, TC-EDO-003 | Yes |

Coverage: 4 cases (1 Positive, 1 Negative, 1 Boundary, 1 Security); High 3, Medium 1.
