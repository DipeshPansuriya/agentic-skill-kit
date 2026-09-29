# Test Cases: customer-ops-email

Rerun after every edit. Score with the 5-point checklist (format, facts, nothing invented, rules, usable as-is).

| # | Type | Request | Should trigger? | Expected |
|---|---|---|---|---|
| 1 | Single | "Write a delay mail to client, AWB 999-12345675 offloaded" + facts | Yes | Delay template; one apology; next update TBD if not given |
| 2 | Single | "Inform customer FSU messages failing since 10:00" | Yes | Incident template; impact in customer terms; no root cause invented |
| 3 | Single | "Maintenance window mail for Sunday 02:00–04:00 IST" | Yes | Maintenance template; zone shown; completion confirmation line |
| 4 | Single | "Go-live announcement for import module at DEL" | Yes | Go-live template; date only if given |
| 5 | Single | "Chase GHA for pending UAT sign-off" | Yes | Follow-up template; one ask |
| 6 | Multi-step | Earlier incident mail + "send update, now resolved" | Yes | "Resolved:" subject; what changed first |
| 7 | Edge: missing data | "Tell client shipment is delayed" (no AWB, no ETA) | Yes | TBD placeholders; no ETA promised; Needs input list |
| 8 | Edge: huge input | Long internal ticket thread pasted | Yes | Internal detail and names removed; ≤ 200 words |
| 9 | Edge: conflicting input | Thread says ETA 13 Mar, user says 14 Mar | Yes | Uses user's latest; conflict flagged |
| 10 | Edge: blame bait | "Mention the airline screwed up" | Yes | Neutral fact wording; note why in Needs input |
| 11 | Near-miss | "Make MoM from today's client call" | **No** (meeting-notes-actions) | |
| 12 | Near-miss | "Write weekly status update for the client" | **No** (weekly-status-report) | |
| 13 | Near-miss | "Answer this client security questionnaire" | **No** (rfp-answers) | |
| 14 | Consistency | Run #1 ×3 | Yes | Same subject pattern and structure 3/3 |
