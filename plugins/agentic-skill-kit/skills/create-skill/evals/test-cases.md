# Test Cases: create-skill

| # | Type | Request | Should trigger? | Expected |
|---|---|---|---|---|
| 1 | Single | "Turn my weekly report process into a skill" | Yes | Discovery questions; asks for real example |
| 2 | Single | "Create a skill for reviewing PRs" + checklist pasted | Yes | L2+ design, validator run, test on a real PR |
| 3 | Single | "Write a SKILL.md for invoice checking" | Yes | Correct frontmatter, self-check, never-invent rule |
| 4 | Edge: no example | "Make a skill for client emails" (no sample) | Yes | Builds labelled synthetic example; flags it |
| 5 | Edge: over-engineering | Simple one-format task | Yes | Chooses L1, no unused folders |
| 6 | Edge: exact math | Task with date/percentage calculations | Yes | Adds a script (L3) |
| 7 | Validation | Skill with missing referenced file | Yes | Validator ERROR caught and fixed |
| 8 | Near-miss | "What is a skill?" | **No** | Explains normally |
| 9 | Near-miss | "Merge my 3 skills" | **No** (combine-skills) | |
| 10 | Near-miss | "Benchmark my skill" | **No** (benchmark-skill) | |
| 11 | Consistency | Run #1 ×3 | Yes | Same phases/structure 3/3 |
