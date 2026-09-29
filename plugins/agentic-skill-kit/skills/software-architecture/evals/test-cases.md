# Test Cases: software-architecture

Rerun after every edit. Score each 0-5: routed correctly · drivers/NFRs with numbers or TBD · ≥ 2 options with correct weighted totals · trade-offs + "when not to use" present · valid Mermaid matching the text.

| # | Type | Request | Should trigger? | Expected |
|---|---|---|---|---|
| 1 | Single (a) | "Design a system to ingest 2M FSU status messages/day from 40 airlines" | Yes | NFR table with sizing math, 2-3 options, C4 L1+L2 + sequence in Mermaid, outbox + idempotent consumer |
| 2 | Single (b) | "Write an ADR: Kafka vs Azure Service Bus for our event bus" | Yes | `adr-template.md` structure, weights = 100%, exact totals, revisit triggers |
| 3 | Single (c) | "What pattern should I use so a booking save and event publish don't get out of sync?" | Yes | Transactional Outbox + Idempotent Consumer, when not to use, logistics example |
| 4 | Single (d) | "Review this architecture" + diagram and 1-page doc | Yes | Findings table, scorecard, top 3 actions; gaps marked "Not documented" |
| 5 | Single (e) | "Should we break our CCS monolith into microservices? 12 devs, 2 teams" | Yes | Decision table scored; likely modular monolith + selective extraction path |
| 6 | Multi | "Design the customs filing module, document the key decision as an ADR, and suggest patterns for retries" | Yes | Sections a → b → c in order; consistent names across sections |
| 7 | Edge: no NFRs | "Design a tracking portal" (no numbers) | Yes | Defaults stated as assumptions, NFR numbers TBD listed in Open questions |
| 8 | Edge: over-engineering bait | "Use CQRS, event sourcing and microservices for our 5-screen admin app" | Yes | Pushes back with trade-offs; recommends simpler option; explains when those patterns fit |
| 9 | Edge: constraint | "On-prem only, no cloud, air-gapped customs site" | Yes | Self-hosted options; managed-service defaults dropped and stated |
| 10 | Near-miss | "Review this pull request for bugs" | **No** (code-review) | Findings table on code, not architecture |
| 11 | Near-miss | "Write the EF Core repository for the Booking entity" | **No** (backend-engineering) | Code, no architecture doc |
| 12 | Near-miss | "Add an index to speed up this AWB query" | **No** (sql-performance-tuning) | Query/index tuning |
| 13 | Near-miss | "Draw the AWB lifecycle state machine" | **No** (workflow-design) | State machine + transition table |
| 14 | Consistency | Run #2 three times | Yes | Same structure, same recommended option, same totals 3/3 |
