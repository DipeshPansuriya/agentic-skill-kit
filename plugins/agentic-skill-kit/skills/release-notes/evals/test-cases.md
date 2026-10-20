# Test Cases: release-notes

Rerun after every edit. Score each with the 0–5 quality checklist (format, facts, nothing invented, rules, usable as-is).

| # | Type | Request | Should trigger? | Expected |
|---|---|---|---|---|
| 1 | Single | "Release notes for sprint 22" + Jira export | Yes | Client + internal variants; fixed category order |
| 2 | Single | "Make a changelog from these commits" + git log | Yes | `parse_commits.py` run; unclassified handled |
| 3 | Single (variant) | "Client-facing what's new for Airline XX, no ticket numbers" | Yes | Benefit language; no IDs/hashes/components |
| 4 | Multi-source | Jira list + commits + known-issue list | Yes | Merged by ticket ID; known issues with workaround |
| 5 | Edge: missing data | Tickets with no version or date | Yes | Version/date TBD; nothing guessed |
| 6 | Edge: huge input | 400 commits | Yes | Grouped; internal-only items kept out of client variant |
| 7 | Edge: conflicting input | Ticket "Won't fix" but commit merged | Yes | Flagged in Needs input; excluded from client variant |
| 8 | Edge: breaking | Commit with `!` and BREAKING CHANGE footer | Yes | Action required with deadline/consequence (TBD if absent) + rollback |
| 9 | Near-miss | "Write an RCA for last night's failed deployment" | **No** (incident-rca) | |
| 10 | Near-miss | "Turn this BRD into user stories" | **No** (requirements-to-stories) | |
| 11 | Near-miss | "Explain Conventional Commits" | **No** | Answer normally |
| 12 | Near-miss | "Write my weekly status for the release team" | **No** | |
| 13 | Consistency | Run #2 ×3 | Yes | Same categories and item counts 3/3 |
