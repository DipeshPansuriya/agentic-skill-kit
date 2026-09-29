# Designing the Test Set

## Mix
| Type | Share | Purpose | Example (status-report skill) |
|---|---|---|---|
| `single` | ~40% | Core task works | "Weekly report from these notes" |
| `multi` | ~20% | Chaining / multiple sources | Notes + Excel + last week's report |
| `near-miss` | ~20% | Must NOT trigger | "What makes a good status report?" |
| `edge` | ~20% | Rules hold under stress | No owners, 3 pages of notes, conflicting data |

## Good test cases
- Use **real wording** the user types, including typos and shorthand.
- Use real (anonymised) inputs; label synthetic ones.
- Write the **expected result** before running: should trigger? which part? must contain?
- Near-misses should be *close*: same topic, different intent.
- For merged skills, add **cross-routing** cases: a request for part A must not load part B.

## Size
| Purpose | Minimum |
|---|---|
| Quick regression after small edit | 10 |
| New skill / version decision | 15–20 |
| Merge decision (A = several skills) | 20+ (≥ 3 per original skill) |

## Consistency
Pick 3 representative cases; run each 3× per version. Compare structure (sections, order, table columns), not wording.

## Maintenance
- Every bug found in real use becomes a new edge case.
- Never delete a case that once failed.
- Version the test set with the skill (`evals/test-cases.md`).
