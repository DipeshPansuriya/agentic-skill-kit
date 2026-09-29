# <Client> <RFP / Questionnaire name>: Draft Answers

**Product in scope:** <product/module> · **Answer bank version:** <date> · **Default tier:** <S/M/L>

## Summary
| ✅ Yes | 🟡 Partial | 🔵 Roadmap | ❌ No | ⚪ Needs input | Total |
|---|---|---|---|---|---|
| | | | | | |

## Answers
| Q-ID | Question | Status | Answer | Source |
|---|---|---|---|---|
| <client ID> | <exact question> | <label> | <answer within tier> | <bank ID / user note / –> |

## Gap log
| Q-ID | Missing or partial fact | Suggested owner | Needed by |
|---|---|---|---|
| | | <Security / Product / Infra / Legal / TBD> | <RFP due date / TBD> |

---
*Assumptions & Needs input (remove before submitting):*
- <defaults used, product scope, bank entries still TO FILL>

---

## Example (fake data)
Bank (filled for the example only): C2 = "Supports Cargo-IMP FWB, FHL, FFM, FSU and Cargo-XML XFWB, XFFM" (Yes); A1 = TO FILL.

| Q-ID | Question | Status | Answer | Source |
|---|---|---|---|---|
| SEC-04 | Is the vendor ISO 27001 certified? | ⚪ Needs input | – | A1 (TO FILL) |
| INT-11 | Does the system receive FWB and FFM messages? | ✅ Yes | Yes. The system supports Cargo-IMP FWB and FFM, and Cargo-XML XFWB and XFFM. | C2 |
| INT-12 | Does it support XFSU? | ⚪ Needs input | – | C2 does not list XFSU |

| Q-ID | Missing or partial fact | Suggested owner | Needed by |
|---|---|---|---|
| SEC-04 | ISO 27001 status, scope, validity | Security | TBD |
| INT-12 | XFSU support confirmation | Product | TBD |
