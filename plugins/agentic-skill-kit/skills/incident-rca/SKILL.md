---
name: incident-rca
description: Turn an incident thread, chat or logs into a blameless RCA with UTC and IST timeline, TTD/TTR, 5 Whys and corrective actions. Use when the user asks for an RCA, postmortem, root cause analysis, or to write up an outage.
---

# Incident Report & Blameless RCA

## Inputs
- War-room chat / Teams or Slack thread (pasted or exported)
- Log extracts, alert emails, monitoring screenshots described in text
- Ticket history (ServiceNow/Jira), customer complaint emails
- Optional: existing draft RCA to complete or correct

Several sources: merge into one timeline. When sources disagree on a time or fact, use the system log over human recollection, and flag the conflict under Needs input.

## Defaults (ask vs assume)
| Setting | Default if not stated | Ask only if |
|---|---|---|
| Audience | Internal (engineering + delivery) | User mentions client/airline/customs authority: switch to Client variant in `references/rca-methods.md` |
| Time zone of un-zoned times | IST | Logs are clearly server UTC |
| Severity | Derive from `references/severity-scale.md` | Impact data is missing entirely |
| Status | Resolved | Input shows it is still ongoing: mark "Monitoring" / "Open" |

Ask at most one question, and only when the answer changes the content. Otherwise assume, and state defaults at the top.

## Steps
1. Read all input once before writing.
2. Put every timestamped line into a file and run `python scripts/timeline.py FILE [--default-tz UTC]`. Use its table and TTD/TTR values as-is; do not compute durations by hand.
3. Extract impact: affected users/customers, shipments/AWBs/ULDs, messages (FWB/FFM/FSU), SLA breached (Y/N, which), duration, financial/regulatory exposure. Keep counts exactly as given.
4. Assign severity with `references/severity-scale.md`; quote the criterion that set it.
5. Describe detection: how (alert, customer, manual), by whom (role), and gap vs expected monitoring.
6. Build the root cause with 5 Whys and contributing factors from `references/rca-methods.md`. Stop at a systemic cause (process, tooling, design), never at a person.
7. Record resolution: immediate fix, workaround, verification, residual risk.
8. List corrective (fix this) and preventive (stop recurrence) actions, each with owner, due date, ticket ID if given.
9. Write lessons learned: what went well, what went badly, where we got lucky.
10. Fill `templates/incident-template.md`. For format reference see `templates/example-rca.md` (fake data).
11. Run the self-check and fix before returning.

## Format
Use `templates/incident-template.md` section order exactly: Summary, Impact, Timeline (UTC + IST), Detection, Root cause (5 Whys + contributing factors), Resolution, Actions, Lessons learned, Assumptions & Needs input.

## Rules
- **Branding only on request:** use plain, neutral formatting by default. Apply a company or brand design skill (colours, fonts, logo, templates) only when the user names that skill or brand in the request; never pick one automatically.
- Never invent times, counts, owners, dates, or causes. Write TBD and list under Needs input.
- Keep IDs exactly as given (AWB, ULD, flight, ticket, host names).
- Blameless: name roles and systems, not people ("on-call engineer", not "Ravi"). Replace "X forgot" with the missing guardrail.
- Every timeline row shows both UTC and IST.
- Label unproven causes "Suspected"; only "Confirmed" when evidence is in the input.
- Every action needs owner + due date + type (Corrective/Preventive); TBD if missing.
- At least one Preventive action must address detection if TTD exceeded the severity target.
- Summary ≤ 5 sentences; whole report ≤ 2 pages.
- Empty section: write "None". Never delete a section.

## Self-check
- [ ] Timeline came from `scripts/timeline.py`; TTD/TTR match its output
- [ ] Severity matches `references/severity-scale.md` and the criterion is quoted
- [ ] 5 Whys end at a systemic cause, not a person
- [ ] No names in blame positions; roles only
- [ ] Every action has owner, date, type; TBDs listed under Needs input
- [ ] Every number/ID matches the input exactly
- [ ] Source conflicts flagged

## Output
Return the report from `templates/incident-template.md`, then an **Assumptions & Needs input** block (defaults used, TBDs, conflicts, suspected-vs-confirmed items) outside the report.

After edits to this skill, rerun `evals/test-cases.md`.
