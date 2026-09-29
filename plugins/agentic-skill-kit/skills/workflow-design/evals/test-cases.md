# Test Cases: workflow-design

Rerun after every edit. Score each 0-5: routed correctly · table before diagram and names match · exceptions/SLAs/idempotency covered · validator PASS or YAML valid where applicable · nothing invented (TBDs listed).

| # | Type | Request | Should trigger? | Expected |
|---|---|---|---|---|
| 1 | Single (b) | "Draw the AWB lifecycle state machine from booked to delivered with exceptions" | Yes | States + transition table incl. offload, holds, discrepancy, cancel; validator PASS line; `stateDiagram-v2` |
| 2 | Single (a) | "Map our export acceptance process across forwarder, GHA and airline" | Yes | Swimlane flowchart + step table with SLAs and exception handling |
| 3 | Single (c) | "Design a GitHub Actions pipeline for our .NET API with staging and prod approval" | Yes | Stage/gate table + YAML from template, rollback plan, OIDC, permissions |
| 4 | Single (c variant) | "Same pipeline but in Azure DevOps" | Yes | Mapped to ADO stages, environments + approvals & checks |
| 5 | Single (d) | "Booking, capacity and payment services: how do we keep them consistent?" | Yes | Orchestrated saga, compensation table, idempotency keys, retry policy, sequence diagram |
| 6 | Multi | "Design the customs hold process, its state machine, and the retry policy for the customs gateway" | Yes | Sections a, b, d with shared names; validator result |
| 7 | Edge: broken table | User pastes a transition table with a dead-end and duplicate | Yes | Validator ERRORs reported and fixed version returned |
| 8 | Edge: missing SLAs | Process notes with no timings | Yes | SLAs "TBD", listed in Needs input; nothing invented |
| 9 | Edge: generic hold | "Add an On Hold state reachable from any state" | Yes | Explains return-state problem; uses separate hold states or guards; validator PASS |
| 10 | Near-miss | "Review this GitHub Actions YAML for security issues" | **No** (code-review) | Findings table, not a new design |
| 11 | Near-miss | "Should we use microservices or a modular monolith?" | **No** (software-architecture) | Architecture decision guide |
| 12 | Near-miss | "Write the SQL table and indexes for shipment status history" | **No** (database-engineering) | Schema/index design |
| 13 | Near-miss | "Implement the retry handler in Spring Boot" | **No** (backend-engineering) | Code, not a workflow design |
| 14 | Consistency | Run #1 three times | Yes | Same states, same transitions, validator PASS 3/3 |
