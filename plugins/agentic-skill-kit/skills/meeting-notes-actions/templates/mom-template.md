# MoM: <Meeting title>, <YYYY-MM-DD or TBD>

**Attendees:** <names / orgs> · **Absent:** <names or None> · **Next meeting:** <date or TBD>
**Context:** <1–2 lines of Info, optional>

## Decisions
1. <Decision, stated as agreed outcome>

## Action items
| # | Action | Owner | Due | Status |
|---|---|---|---|---|
| 1 | <Verb + object + ID> | <Name / TBD> | <date / TBD> | 🆕 Open |

## Open questions
| # | Question | Who answers | By |
|---|---|---|---|

## Risks
| Risk | Impact | Mitigation / owner |
|---|---|---|

## Follow-up email
**Subject:** MoM: <Meeting title>, <date> | <n> actions
Hi all,
Thanks for your time today. Summary below.
**Decisions:** <bullets>
**Actions:** <table above, or top items>
**Next meeting:** <date or TBD>
Please reply by <date> if anything is missed.
Regards, <sender>

---
*Assumptions & Needs input (remove before sending):*
- <defaults used, TBDs, conflicts, unknown shorthand>

---

## Example (fake data)
**Input notes:**
> call w/ SkyFreight GHA 12-Mar. RK, Priya, Anil(client). FFM not reaching CCS for flt XY-204 since mon. Anil - their side firewall change? RK will check logs today. priya: agreed to switch to backup SITA addr till fix. UAT for FSU RCS msg - kal ho jayega. Anil to share new IP - date nahi bola. risk: Thursday peak, 40+ AWBs pending manifest.

**Output (extract):**
| # | Action | Owner | Due | Status |
|---|---|---|---|---|
| 1 | Check logs for FFM not reaching CCS, flight XY-204 | RK | 12-Mar (today) | 🆕 Open |
| 2 | Share new IP after firewall change | Anil (SkyFreight) | TBD | ⚪ TBD |
| 3 | Complete UAT for FSU RCS message | TBD | 13-Mar ("kal") | ⚪ TBD |

Decision: Switch to backup SITA address until fix (agreed by Priya).
Risk: Thursday peak, 40+ AWBs pending manifest. Impact: manifest delay. Mitigation: backup SITA route (Priya).
Needs input: owner for UAT; Anil's due date; year of meeting.
