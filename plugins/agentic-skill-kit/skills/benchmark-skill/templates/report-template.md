# Benchmark Report: <skill-name>

**Date:** <YYYY-MM-DD> · **A (baseline):** <label> · **B (candidate):** <label> · **Cases:** <n> (<runs> runs)

## Verdict: <SHIP / FIX & RETEST / KEEP BASELINE>
<One sentence with the 1–2 numbers that decided it.>

## Scorecard
| Metric | A | B | Δ | Target | Met? |
|---|---|---|---|---|---|
| Trigger accuracy | | | | ≥ 90% | |
| Recall | | | | ≥ 95% | |
| False-trigger rate | | | | ≤ 10% | |
| Routing accuracy | | | | 100% | |
| Avg quality (0–5) | | | | ≥ 4.0 | |
| Critical failures | | | | 0 | |
| Consistency | | | | 100% | |
| Avg tokens / seconds | | | | ≤ A × 1.3 | |

## By case type
| Type | A quality | B quality | A trigger acc | B trigger acc |
|---|---|---|---|---|
| single | | | | |
| multi | | | | |
| edge | | | | |
| near-miss | – | – | | |

## Critical failures
- <case id: what happened> or "None"

## Top fixes
1. <Fix>: cases <ids>
2. <Fix>: cases <ids>
3. <Fix>: cases <ids>

## Files
- Test set: `evals/test-cases.md`
- Results: `results.csv`
- Outputs: `outputs/<version>/`
