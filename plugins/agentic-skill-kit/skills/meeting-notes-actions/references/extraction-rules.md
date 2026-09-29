# Extraction Rules

## Line classification
| Class | Signals in notes | Goes to |
|---|---|---|
| Decision | agreed, final, approved, go ahead, "done hai", "fix kar diya", "chalega" | Decisions |
| Action | will, to do, pls, "karega", "bhejo", "check karo", AI:, @name | Action items |
| Open question | ?, tbc, "confirm karna hai", "pata nahi", pending clarity | Open questions |
| Risk | may slip, dependency, blocked, "problem ho sakta hai", SLA, cut-off | Risks |
| Info | status statements with no follow-up | Context line in header (max 2) |
| Noise | greetings, jokes, audio issues, "can you hear me" | Drop |

## Common shorthand (logistics + Hinglish)
| Written | Meaning |
|---|---|
| AI / A/I | Action item |
| EOD / EOW / COB | End of day / week / close of business |
| kal | Tomorrow (or yesterday by context: flag if unclear) |
| parso | Day after tomorrow (or day before: flag if unclear) |
| karega / karegi / dekh lega | Will do / will check (action for that person) |
| ho jayega | Will get done (not a commitment unless owner named) |
| UAT / PROD / SIT | Test / production / integration environments |
| FWB / FHL / FFM / FSU | Cargo-IMP / Cargo-XML messages (keep as written) |
| GHA / CCS / FF / CHA | Ground handler / cargo community system / freight forwarder / customs broker |

Unknown abbreviation: keep it as written and add it to Needs input.

## Speakers
- Map initials to full names only when the notes or attendee list make it certain.
- Two people with the same initial: keep initials and flag.
- Speaker who "will check" owns the action, even if someone else raised it.

## Status values
| Status | Use when |
|---|---|
| 🆕 Open | New action, not started |
| 🔄 In progress | Notes say started / partly done |
| ✅ Done | Completed during or before the meeting |
| ⏩ Slipped | Carried over from previous MoM, past its due date |
| ⚪ TBD | Owner or due missing |

## Conflicts
| Situation | Handling |
|---|---|
| Two sources give different owners/dates | Use the later source, flag both values |
| Decision later reversed in the same notes | Keep the final one; note "(changed from X)" |
| Action with two owners | One primary owner; others in a "Support" note |
