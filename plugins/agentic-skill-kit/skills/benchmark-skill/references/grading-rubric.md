# Grading Rubric (0/1 per check, max 5)

| Column | Check | 1 = pass when… | Common fail |
|---|---|---|---|
| `q_format` | Format | All required sections present, in order, with correct tables | Missing section, reordered, table became bullets |
| `q_facts` | Completeness | Every key fact from the input appears (or is deliberately dropped as noise) | Blocker or metric missing |
| `q_no_invent` | Faithfulness | No invented owners, dates, numbers, IDs, status | "Owner: Priya" when input had no owner |
| `q_rules` | Rules | Length, tone, audience, TBD handling, exact IDs all respected | Over length; internal names in client version |
| `q_usable` | Usability | Could be sent as-is (or with ≤ 1 trivial edit) | Needs rewriting |

## Critical failures (flag in `critical` column = 1)
- Invented data presented as fact
- Confidential/internal info in an external-audience output
- Wrong audience or wrong task entirely
- Destructive or unsafe action suggested

A critical failure blocks SHIP even if averages are higher.

## Trigger & routing columns
| Column | Value |
|---|---|
| `triggered` | 1 if the skill loaded, 0 if not |
| `routed_ok` | 1 correct part loaded, 0 wrong part, blank if not applicable |

## Blind grading
Rename outputs to random IDs, grade, then map back. If grading alone, wait until all outputs are generated, shuffle, then grade.
