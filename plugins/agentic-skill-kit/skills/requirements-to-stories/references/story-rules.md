# Story Writing Rules

## INVEST check
| Letter | Pass if | Typical fix |
|---|---|---|
| **I**ndependent | Can be built and released without another story in the same sprint | Move shared part to its own story; record dependency |
| **N**egotiable | Describes outcome, not UI pixels or implementation | Remove solution detail to notes |
| **V**aluable | A persona gains something visible | Merge technical tasks into the value story |
| **E**stimable | Team can size it; no major unknowns | Add a spike story; list the question |
| **S**mall | ≤ 8 points / fits one sprint | Split (patterns below) |
| **T**estable | Gherkin criteria have observable Then clauses | Replace "fast"/"easy" with measurable criteria or an open question |

## Splitting patterns
| Pattern | Logistics example |
|---|---|
| Workflow step | Create booking · Amend booking · Cancel booking |
| Business rule variant | General cargo · DGR · Perishable (PER) · Valuable (VAL) |
| Data/message type | FWB · FHL · FSU/RCS |
| Channel | Web portal · API · EDI |
| Happy path first, then exceptions | Issue e-DO · Reject e-DO on unpaid charges |
| Role | Forwarder view · GHA view · Airline view |

## Gherkin
```
Scenario: <outcome in plain words>
  Given <precondition / state>
  And <more context>
  When <single user action or event>
  Then <observable result>
  And <more results>
```
- One When per scenario. Use concrete but fake example data (AWB 000-00000000).
- Include at least one negative scenario (invalid input, missing permission, system down).
- Use Scenario Outline + Examples table for 3+ data variants.

## Story-point hint
| Points | Signal |
|---|---|
| 1–2 | Config/text change, one screen, no integration |
| 3 | One screen + validation + API, known pattern |
| 5 | New flow or one external integration (airline host, customs, payment) |
| 8 | Several screens + integration + unknowns; consider splitting |
| 13+ | Too big: must split or run a spike |
