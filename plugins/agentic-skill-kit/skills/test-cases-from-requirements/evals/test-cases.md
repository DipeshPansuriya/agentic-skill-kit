# Test Cases: test-cases-from-requirements

Rerun after every edit. Score each with the 0–5 quality checklist (format, facts, nothing invented, rules, usable as-is).

| # | Type | Request | Should trigger? | Expected |
|---|---|---|---|---|
| 1 | Single | "Write test cases for this story" + story with Gherkin | Yes | Table + traceability + coverage; positive and negative per AC |
| 2 | Single | "UAT scripts for the e-DO module" + BRD extract | Yes | UAT level; business-language steps |
| 3 | Single (variant) | "Test cases for AWB weight validation 1–1000 kg" | Yes | Boundary 0/1/1000/1001; equivalence classes |
| 4 | Multi-source | 3 stories + API spec | Yes | Merged by req ID; API negative cases; no duplicates |
| 5 | Edge: missing data | "Test the booking screen" with no rules | Yes | Assumed values marked; many Needs input items; nothing invented |
| 6 | Edge: huge input | 40 acceptance criteria | Yes | All traced; coverage counts correct |
| 7 | Edge: conflicting input | Story says max 99 pieces, spec says 999 | Yes | Cases marked Blocked: conflict; flagged |
| 8 | Variant: automation | "…and tell me which to automate in Playwright" | Yes | Hand-off table + skeleton from reference |
| 9 | Near-miss | "Write user stories from this BRD" | **No** (requirements-to-stories) | |
| 10 | Near-miss | "Write a Playwright script for login" (no requirement) | **No** | Code task, answer normally |
| 11 | Near-miss | "RCA for the bug that escaped testing" | **No** (incident-rca) | |
| 12 | Near-miss | "What is boundary value analysis?" | **No** | Answer normally |
| 13 | Consistency | Run #1 ×3 | Yes | Same IDs scheme and case count ±1, 3/3 |
