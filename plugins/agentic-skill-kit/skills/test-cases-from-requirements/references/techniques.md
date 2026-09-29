# Test Design Techniques

| Technique | Use when | How | Min cases |
|---|---|---|---|
| **Equivalence partitioning** | Input with valid/invalid classes | One case per class (valid, each invalid kind) | 1 per class |
| **Boundary value** | Numeric/date/length limits | min-1, min, max, max+1 (and min+1/max-1 for critical) | 4 per limit |
| **Decision table** | 2+ conditions combine to an outcome | Table of condition combos, one case per rule column; collapse "don't care" | 1 per column |
| **State transition** | Status lifecycle | Every valid transition + key invalid ones + terminal states | valid + ≥ 2 invalid |
| **Error guessing** | Known weak spots | Nulls, duplicates, special chars, time zones, concurrency, timeouts | as needed |

## Logistics examples (fake data)
**Equivalence partitioning: AWB number (3-digit prefix + 8 digits, mod-7 check digit)**
| Class | Example | Expected |
|---|---|---|
| Valid | 000-00000000 | Accepted |
| Wrong length | 000-1234567 | "Invalid AWB" (assumed message) |
| Non-numeric | 000-1234ABCD | Rejected |
| Bad check digit | 000-00000001 | Rejected |

**Boundary: piece weight limit 1–1000 kg (assumed)**: 0, 1, 1000, 1001.

**Decision table: e-DO issuance**
| Condition | R1 | R2 | R3 | R4 |
|---|---|---|---|---|
| Charges paid | Y | Y | N | N |
| Customs cleared | Y | N | Y | N |
| **Outcome** | Issue | Block: customs | Block: charges | Block: both |

**State transition: AWB status**
| From | Event | To | Valid? |
|---|---|---|---|
| Booked | Cargo received (RCS) | RCS | Yes |
| RCS | Departed (DEP) | DEP | Yes |
| DEP | Arrived (ARR) | ARR | Yes |
| ARR | Delivered (DLV) | DLV | Yes |
| Booked | Delivered | DLV | No: must reject |
| DLV | Any | - | No: terminal |

## Security checklist (add where relevant)
- User of customer A cannot see/modify customer B's AWBs (IDOR)
- Role without permission gets 403, not hidden button only
- Injection in search/text fields (SQL, script) is neutralised
- File upload: type, size, malware scan
- Session timeout and logout invalidate token
- No personal/commercial data in error messages or logs
