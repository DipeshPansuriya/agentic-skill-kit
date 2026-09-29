# Test Cases: kpi-analysis

Rerun after every edit. Score each with the 0–5 quality checklist (format, facts, nothing invented, rules, usable as-is).

| # | Type | Request | Should trigger? | Expected |
|---|---|---|---|---|
| 1 | Single | "Analyse this week's KPI export" + `templates/sample-kpi.csv` | Yes | Script run; dwell and OTP flagged; narrative ≤ 120 words |
| 2 | Single | "Write commentary on these metrics for my manager" + Excel | Yes | Headline + flags table + actions |
| 3 | Single (variant) | "Leadership version, 3 lines" | Yes | Narrative ≤ 60 words; numbers match script |
| 4 | Multi-source | Two CSVs (ops + EDI KPIs) + context note "peak season" | Yes | Combined; driver cites peak season only where supported |
| 5 | Edge: missing data | CSV with no target column and 2 weeks only | Yes | vs Target n/a; INSUFFICIENT-HISTORY; no invented targets |
| 6 | Edge: huge input | 52 weeks × 40 metrics | Yes | Latest-week table + top movers; no full dump unless asked |
| 7 | Edge: conflicting input | Same metric/week in two files with different values | Yes | Most recent kept; conflict in Needs input |
| 8 | Edge: wide format | One column per metric | Yes | Reshaped to long per reference, then script |
| 9 | Near-miss | "Build a chart dashboard of our KPIs" | **No** (dataviz) | |
| 10 | Near-miss | "Weekly status report for my team" | **No** (weekly-status-report) | |
| 11 | Near-miss | "RCA for why dwell time spiked last Tuesday's outage" | **No** (incident-rca) | |
| 12 | Near-miss | "What KPIs should a GHA track?" | **No** | Answer normally |
| 13 | Consistency | Run #1 ×3 | Yes | Identical numbers and flags 3/3 |
