# Test Cases: meeting-notes-actions

Rerun after every edit. Score with the 5-point checklist (format, facts, nothing invented, rules, usable as-is).

| # | Type | Request | Should trigger? | Expected |
|---|---|---|---|---|
| 1 | Single | "Make MoM from these notes" + rough notes | Yes | Template sections in order; email ≤ 150 words |
| 2 | Single | "Action items from today's client call" + Hinglish notes | Yes | Hinglish normalised; owners mapped; "kal" handled per rules |
| 3 | Single | "Draft follow-up mail after the Emirates onboarding call" + notes | Yes | Client-safe email; no internal remarks |
| 4 | Multi-source | Two attendees' notes of the same meeting | Yes | Merged; owner/date conflicts flagged |
| 5 | Multi-step | Notes + previous MoM | Yes | Carried-over actions marked Done / Slipped / Open |
| 6 | Edge: missing data | Notes with no names or dates | Yes | TBD everywhere; Needs input lists every gap; nothing invented |
| 7 | Edge: huge input | 60-min transcript, 5 speakers | Yes | Noise dropped; email still ≤ 150 words |
| 8 | Edge: conflicting input | Decision made, then reversed later in notes | Yes | Final decision kept with "(changed from X)" |
| 9 | Edge: IDs | Notes with AWB 176-12345675, ULD AKE12345XY | Yes | IDs copied exactly |
| 10 | Near-miss | "Write my weekly status report from these notes" | **No** (weekly-status-report) | |
| 11 | Near-miss | "Send client a delay notice for AWB 176-12345675" | **No** | |
| 12 | Near-miss | "Turn these steps into an SOP" | **No** (sop-writer) | |
| 13 | Near-miss | "How do I run a good meeting?" | **No** | Answer normally |
| 14 | Consistency | Run #1 ×3 | Yes | Same sections, same actions and owners 3/3 |
