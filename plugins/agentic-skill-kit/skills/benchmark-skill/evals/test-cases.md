# Test Cases: benchmark-skill

| # | Type | Request | Should trigger? | Expected |
|---|---|---|---|---|
| 1 | Single | "Benchmark my weekly-status-report skill vs no skill" | Yes | A/B defined; ≥ 15 cases; script run; verdict |
| 2 | Single | "Did my edit break anything? Compare v1.2 and v1.3" | Yes | Regression framing; reuses saved test set |
| 3 | Multi | "Test if my merged tech-toolkit beats the 3 separate skills" | Yes | ≥ 20 cases; routing accuracy measured |
| 4 | Edge: tiny set | User offers only 5 test prompts | Yes | Expands to ≥ 15 or refuses a verdict; explains why |
| 5 | Edge: critical | Candidate invents an owner once | Yes | Critical failure blocks SHIP |
| 6 | Edge: tie | Quality differs by 0.1 | Yes | Reported as tie |
| 7 | Edge: cost | Candidate 1.6× tokens, same quality | Yes | FIX & RETEST (cost) |
| 8 | Near-miss | "Benchmark these two laptops" | **No** | |
| 9 | Near-miss | "Create a skill for invoices" | **No** (create-skill) | |
| 10 | Near-miss | "Merge my skills" | **No** (combine-skills) | |
| 11 | Consistency | Run #1 ×3 | Yes | Same report structure 3/3 |
