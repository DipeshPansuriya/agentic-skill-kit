# Test Cases: sop-writer

Rerun after every edit. Score with the 5-point checklist (format, facts, nothing invented, rules, usable as-is).

| # | Type | Request | Should trigger? | Expected |
|---|---|---|---|---|
| 1 | Single | "Write an SOP for export AWB creation" + rough steps | Yes | All 8 sections; one action per step; expected results |
| 2 | Single | "Make a work instruction from these screenshots" + screen descriptions | Yes | Fig. references; UI labels bold and exact |
| 3 | Single | "Process document for ULD build-up check" + steps | Yes | Roles not names; safety checks as separate bold steps |
| 4 | Multi-source | Steps from two operators that differ | Yes | Order merged; differences flagged |
| 5 | Multi-step | Existing SOP v1.0 + "add the new e-DO step" | Yes | v1.1 with version-history row; history kept |
| 6 | Edge: missing data | Steps with no screen names or results | Yes | "TBD (confirm)" results; Needs input lists screens to capture |
| 7 | Edge: huge input | 60 rough steps | Yes | Split into sub-procedures (5.1, 5.2); ≤ 25 steps each |
| 8 | Edge: conflicting input | "Click Submit" in one line, "Click Save" in another for same step | Yes | Conflict flagged, not guessed |
| 9 | Edge: gap | Step jumps from login to printing label | Yes | Flow gap flagged; no invented middle steps |
| 10 | Near-miss | "Summarise this process meeting and list actions" | **No** (meeting-notes-actions) | |
| 11 | Near-miss | "Email clients about the new booking process go-live" | **No** | |
| 12 | Near-miss | "Does our product support audit trails? Fill the RFP" | **No** (rfp-answers) | |
| 13 | Near-miss | "What is an SOP?" | **No** | Answer normally |
| 14 | Consistency | Run #1 ×3 | Yes | Same sections and step count 3/3 |
