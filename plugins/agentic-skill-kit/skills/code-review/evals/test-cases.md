# Test Cases: code-review

Rerun after every edit. Score each with the quality checklist (0-5): format/order · every finding has real File:line · nothing invented · rules respected (Verify labels, no nitpicks, fixes) · verdict correct.

| # | Type | Request | Should trigger? | Expected |
|---|---|---|---|---|
| 1 | Single | "Review this PR" + C# controller diff building SQL from `awbNo` | Yes | High/Security row at exact line, parameterized fix, verdict Request changes |
| 2 | Single | "Can you check this Python consumer before I merge?" (Kafka handler, no dedupe) | Yes | Idempotency row (High or Verify), DLQ/timeout checks, concrete fix |
| 3 | Single | "Look over this Angular component" with nested subscribes, no unsubscribe | Yes | Med rows for leak + nested subscribe; `switchMap` / `takeUntilDestroyed` fix |
| 4 | Multi | Diff across Java service + SQL migration + React form | Yes | All three stack sections applied; cross-file issue (e.g., column rename breaks API) in one row |
| 5 | Edge: clean code | Small, correct, well-tested diff | Yes | "No findings", verdict Approve, lists what was checked; nothing invented |
| 6 | Edge: no line numbers | Pasted snippet without file names | Yes | Cites function/method names; does not invent paths or lines |
| 7 | Edge: uncertain | Diff calls a helper not shown | Yes | Row labelled **Verify:** with what to check; verdict not driven by it alone |
| 8 | Edge: focus | "Security review only" | Yes | Only Security rows; states scope; OWASP 2025 IDs |
| 9 | Edge: nitpicks | Diff with inconsistent spacing and naming only | Yes | No style rows; Approve; mentions linter if relevant |
| 10 | Edge: large | 1,500-line diff | Yes | Findings ranked, duplicates merged, "Not reviewed" note for skipped generated files |
| 11 | Near-miss | "Write a REST endpoint for booking cancellation in .NET" | **No** (backend-engineering) | Writes code; no review table |
| 12 | Near-miss | "Design the schema for ULD tracking" | **No** (database-engineering) | Schema design, not a review |
| 13 | Near-miss | "Should we use CQRS for our booking service?" | **No** (software-architecture) | Architecture guidance |
| 14 | Near-miss | "Set up a GitHub Actions pipeline that runs code review linting" | **No** (workflow-design) | Pipeline YAML, not a findings table |
| 15 | Consistency | Run #1 three times | Yes | Same High finding, same verdict, same table columns 3/3 |
