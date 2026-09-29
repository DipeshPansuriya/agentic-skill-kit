# Benchmark Test Set: weekly-status-report

Rerun after every edit. Score with guide 03 (quality checklist 0–5).

| # | Type | Request | Expected |
|---|---|---|---|
| 1 | Single | "Make my weekly report from these notes: …" | Triggers; Manager + Email defaults stated |
| 2 | Single | "Weekly update for leadership, keep it short" + notes | ≤150 words, overall RAG, top risks, one ask |
| 3 | Single | "Client status update for DHL onboarding" + notes | No internal names/blockers; ≤250 words |
| 4 | Multi-source | Notes + pasted Excel rows + email thread | Merged; conflicts flagged in Needs input |
| 5 | Week-over-week | Notes + last week's report | "Carried over" filled; metric deltas ▲/▼ |
| 6 | Edge: missing data | Notes with no owners/dates | "TBD" everywhere + Needs input list; nothing invented |
| 7 | Edge: all blockers | Notes where 3 items are stuck | Overall Red; each Red has impact/owner/action/date |
| 8 | Edge: huge input | 2 pages of notes | Still within length limit |
| 9 | Channel | "Post this in Teams" | TL;DR + RAG + ≤5 bullets |
| 10 | Near-miss | "What should a good status report include?" | Should NOT trigger; answer normally |
| 11 | Near-miss | "Summarise this meeting" | Should NOT trigger (not a weekly status) |
| 12 | Consistency | Run #1 three times | Same structure 3/3 |
