# Test Cases: incident-rca

Rerun after every edit. Score each with the 0–5 quality checklist (format, facts, nothing invented, rules, usable as-is).

| # | Type | Request | Should trigger? | Expected |
|---|---|---|---|---|
| 1 | Single | "Write an RCA from this war-room chat" + Teams thread | Yes | Full template; timeline via script; UTC + IST columns |
| 2 | Single | "Postmortem for yesterday's FFM outage, here are the logs" | Yes | Severity with quoted criterion; 5 Whys end at systemic cause |
| 3 | Single (variant) | "Incident report for Airline XX, client-facing" | Yes | Client variant: no host/owner names, no internal tooling |
| 4 | Multi-source | Chat + server logs (UTC) + customer email (IST) | Yes | One merged timeline; log time wins; conflict flagged |
| 5 | Edge: missing data | Thread with no resolution time or owners | Yes | TTR "TBD (marker not found)"; owners TBD; Needs input list |
| 6 | Edge: huge input | 800-line log dump | Yes | Only key events in timeline; report ≤ 2 pages |
| 7 | Edge: conflicting input | Chat says fixed 15:10, log shows errors until 15:40 | Yes | Uses log; conflict under Needs input |
| 8 | Edge: blame | Chat says "Rahul pushed a bad config" | Yes | Rewritten blameless (roles, missing guardrail) |
| 9 | Edge: ongoing | Incident still open | Yes | Status Open/Monitoring; no invented resolution |
| 10 | Near-miss | "Write release notes for the hotfix we shipped" | **No** (release-notes) | |
| 11 | Near-miss | "Create test cases so this bug never comes back" | **No** (test-cases-from-requirements) | |
| 12 | Near-miss | "Why is our on-time % down this week?" + KPI CSV | **No** (kpi-analysis) | |
| 13 | Near-miss | "What is a good RCA process?" | **No** | Answer normally |
| 14 | Consistency | Run #1 ×3 | Yes | Same sections, same TTD/TTR 3/3 |
