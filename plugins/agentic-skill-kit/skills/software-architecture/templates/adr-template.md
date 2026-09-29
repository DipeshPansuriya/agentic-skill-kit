# ADR-<NNN>: <Short decision title in active voice>

| Field | Value |
|---|---|
| Status | Proposed / Accepted / Superseded by ADR-<NNN> / Deprecated |
| Date | <YYYY-MM-DD> |
| Deciders | <names / roles> |
| Consulted | <names / roles> |
| Related | <tickets, ADRs, docs> |

## Context
<Problem, forces and constraints in 3-6 sentences. Include volumes and NFR numbers.>

## Decision drivers
| # | Driver | Weight |
|---|---|---|
| 1 | <e.g., Handle 500 msg/s peak with p95 < 60 s end-to-end> | <30%> |
| 2 | <e.g., Operable by current team without new platform skills> | <25%> |
| 3 | <e.g., Run cost ≤ budget> | <20%> |
| 4 | <e.g., Time to deliver> | <15%> |
| 5 | <e.g., Vendor lock-in / portability> | <10%> |
| | **Total** | **100%** |

## Options considered
1. **<Option A>**: <one line>
2. **<Option B>**: <one line>
3. **<Option C / do nothing / simplest>**: <one line>

## Weighted trade-off (scores 1-5, higher is better)
| Driver (weight) | Option A | Option B | Option C |
|---|---|---|---|
| <Driver 1> (<30%>) | <n> | <n> | <n> |
| <Driver 2> (<25%>) | <n> | <n> | <n> |
| <Driver 3> (<20%>) | <n> | <n> | <n> |
| <Driver 4> (<15%>) | <n> | <n> | <n> |
| <Driver 5> (<10%>) | <n> | <n> | <n> |
| **Weighted total** | **<x.xx>** | **<x.xx>** | **<x.xx>** |

## Decision
We will <chosen option> because <top 2 reasons tied to drivers>.

## Consequences
| Type | Consequence |
|---|---|
| Positive | <…> |
| Negative / accepted trade-off | <…> |
| Risk | <risk> → mitigation: <…> |

## Revisit when
- <Trigger, e.g., peak volume exceeds 2,000 msg/s>
- <Trigger, e.g., second team takes ownership of the module>

## Implementation notes (optional)
<Key steps, migration, diagram link>
