# Test Cases: combine-skills

| # | Type | Request | Should trigger? | Expected |
|---|---|---|---|---|
| 1 | Single | "Merge my code-review, api-testing and deploy-check skills" | Yes | Inventory → score shown → build |
| 2 | Single | "Consolidate these 2 report skills into one" + pasted SKILL.mds | Yes | Conflicts logged; routing table |
| 3 | Edge: unrelated | "Combine my SQL tuning and HR email skills" | Yes | Score ≤ 4 → recommends NOT merging |
| 4 | Edge: partial | 3 skills, one outlier | Yes | Partial merge proposed |
| 5 | Edge: conflict | Two severity scales | Yes | One chosen, logged with reason |
| 6 | Edge: built-in skill | Includes a plugin/built-in skill | Yes | Copies content to new name; doesn't edit original |
| 7 | Coverage | Any merge | Yes | Every original trigger + rule accounted for |
| 8 | Near-miss | "Create a new skill for invoices" | **No** (create-skill) | |
| 9 | Near-miss | "Compare two versions of my skill" | **No** (benchmark-skill) | |
| 10 | Near-miss | "Merge these two PDFs" | **No** | |
| 11 | Consistency | Run #1 ×3 | Yes | Same phases 3/3 |
