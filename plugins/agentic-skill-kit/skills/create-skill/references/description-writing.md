# Writing the Description

The description is the **only** part read for every request. It decides whether the skill triggers.

## Formula
`<What it does, with the key output>. Use when the user <verb phrases they actually type>[, including <edge phrasings>].`

## Checklist
- [ ] Starts with a verb: "Turn…", "Review…", "Build…"
- [ ] Names the output: "one-page report", "PR review with severity table"
- [ ] "Use when…" lists 3–6 real trigger phrases
- [ ] Mentions input types if distinctive (CSV, Jira export, AWB list)
- [ ] ≤ 250 chars ideal, ≤ 1024 max
- [ ] No vague words alone: "helps", "assists", "various"

## Tuning
| Problem in testing | Fix |
|---|---|
| Doesn't trigger on a valid request | Add that phrasing to "Use when…" |
| Triggers on general questions (near-misses) | Make the output concrete; add "for <audience>" or "from <input>" |
| Competes with another skill | Add the distinguishing input/output; consider merging (see combine-skills) |

## Examples
| ❌ | ✅ |
|---|---|
| Helps write reports. | Turn weekly notes or tracker exports into a RAG status report for managers or clients. Use when the user asks for a weekly report, status update, or progress summary. |
| Code review skill. | Review code or a pull request against the team checklist and return a severity-ranked findings table. Use when the user asks to review code, check a PR, or audit a diff. |
