# Test Cases: rfp-answers

Rerun after every edit. Score with the 5-point checklist (format, facts, nothing invented, rules, usable as-is).

| # | Type | Request | Should trigger? | Expected |
|---|---|---|---|---|
| 1 | Single | "Fill this RFP for the airline" + 30 questions | Yes | Every question labelled; answers cite bank IDs; gap log |
| 2 | Single | "Answer this client security questionnaire" + rows | Yes | Tier S/M; TO FILL entries labelled Needs input |
| 3 | Single | "Vendor assessment form from the airport, 150-char limit per answer" | Yes | Each answer within 150 chars; label first |
| 4 | Multi-source | Questions + user's notes + previous answers to same client | Yes | Consistent with previous; conflicts flagged |
| 5 | Edge: missing data | Answer bank entirely TO FILL | Yes | All Needs input; nothing factual invented; full gap log |
| 6 | Edge: huge input | 400-row Excel questionnaire | Yes | Q-IDs kept; repeated questions answered identically; summary counts correct |
| 7 | Edge: conflicting input | Bank B5 says RTO 4h, user note says 2h | Yes | Needs input; conflict in gap log |
| 8 | Edge: pressure to overclaim | "Just say Yes to SOC 2, we'll get it" | Yes | Refuses Yes without bank fact; Roadmap only if bank says |
| 9 | Edge: no question IDs | Questions pasted as plain text | Yes | Numbered Q-1, Q-2 in order |
| 10 | Near-miss | "Write an SOP for our incident response process" | **No** (sop-writer) | |
| 11 | Near-miss | "Email the client that the security review is scheduled" | **No** (customer-ops-email) | |
| 12 | Near-miss | "Action items from the RFP kickoff call" | **No** (meeting-notes-actions) | |
| 13 | Near-miss | "What is ISO 27001?" | **No** | Answer normally |
| 14 | Consistency | Run #1 ×3 | Yes | Same labels and bank citations 3/3 |
