# Metrics & Decision Rules

## Metrics (computed by `scripts/score_benchmark.py`)
| Metric | Formula | Target |
|---|---|---|
| Trigger accuracy | correct trigger decisions / all runs | ≥ 90% |
| Recall | triggered / should-trigger runs | ≥ 95% |
| Precision | should-trigger among triggered / triggered | ≥ 90% |
| False-trigger rate | triggered near-misses / near-miss runs | ≤ 10% |
| Routing accuracy | routed_ok=1 / routed rows | 100% on single-task |
| Avg quality | mean of 5 checks (0–5) on should-trigger runs | ≥ 4.0 |
| Critical failures | count of critical=1 | 0 |
| Consistency | % of repeated cases with identical `structure` across runs | 100% |
| Cost | mean tokens, mean seconds | ≤ baseline × 1.3 |

## Decision rules (applied in order)
1. **KEEP BASELINE** if candidate has any critical failure that baseline doesn't.
2. **FIX & RETEST** if candidate misses any target above (trigger accuracy, false-trigger rate, quality ≥ 4.0, consistency).
3. **KEEP BASELINE** if candidate quality < baseline by ≥ 0.2, or trigger accuracy lower by ≥ 5 pts.
4. **FIX & RETEST (cost)** if cost > baseline × 1.3 with no quality gain ≥ 0.2.
5. **SHIP** if candidate ≥ baseline on trigger accuracy and quality (ties allowed), and all targets are met.

## Diagnosis
| Symptom | Likely cause | Fix |
|---|---|---|
| Low recall | Description missing phrasings | Add trigger phrases |
| High false-trigger rate | Description too broad | Make output/input concrete |
| Wrong routing | Ambiguous routing table | One row per request type; add fallback |
| q_format failures | No template / vague format | Add `templates/` file |
| q_no_invent failures | Missing "never invent" rule | Add rule + self-check item |
| Low consistency | Too much freedom | Stricter format; add example |
| High cost | Everything in SKILL.md | Move detail to references |
