# Test Cases: requirements-to-stories

Rerun after every edit. Score each with the 0–5 quality checklist (format, facts, nothing invented, rules, usable as-is).

| # | Type | Request | Should trigger? | Expected |
|---|---|---|---|---|
| 1 | Single | "Write user stories from this client email" + email | Yes | Epics + stories + Gherkin + open questions |
| 2 | Single | "Break down this BRD section into a backlog" | Yes | Epics by capability; traceability REQ to story |
| 3 | Single (variant) | "Give me a Jira import CSV for these requirements" | Yes | Valid CSV, same column count each row, epics first |
| 4 | Multi-source | Email + BRD extract + meeting notes | Yes | Merged; duplicates removed; conflicts in Open questions |
| 5 | Edge: missing data | One-line vague ask: "Need a better tracking screen" | Yes | Minimal story + spike; many open questions; nothing invented |
| 6 | Edge: huge input | 30-page BRD | Yes | Epic-level first; every REQ traced; big stories split |
| 7 | Edge: conflicting input | Email says 48 h DO validity, BRD says 72 h | Yes | Conflict flagged; no silent choice |
| 8 | Edge: technical ask | "Story: migrate DB to Postgres" | Yes | Reframed as enabler/task, flagged as not user-facing |
| 9 | Near-miss | "Write test cases for story ST-12" | **No** (test-cases-from-requirements) | |
| 10 | Near-miss | "Draft release notes for sprint 14 stories" | **No** (release-notes) | |
| 11 | Near-miss | "What is the INVEST principle?" | **No** | Answer normally |
| 12 | Near-miss | "Write a status update on the backlog" | **No** | |
| 13 | Consistency | Run #1 ×3 | Yes | Same epics and story count 3/3 |
