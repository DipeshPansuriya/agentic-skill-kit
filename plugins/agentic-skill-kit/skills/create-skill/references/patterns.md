# Body Patterns

## Recommended section order
1. **Inputs:** what the skill accepts and how to handle several sources
2. **Settings/defaults:** audience, channel, period; which to ask vs. assume
3. **Steps:** numbered; each step one action
4. **Format:** exact structure (or point to `templates/`)
5. **Rules:** short imperative bullets
6. **Self-check:** checkbox list run before returning
7. **Output:** what to return, plus an "Assumptions / Needs input" block

## Degrees of freedom
| Task type | How strict | Write it as |
|---|---|---|
| Fragile / exact (dates, calculations, file formats) | Very strict | Script + "run X, don't compute by hand" |
| Structured output (reports, reviews) | Strict format, flexible wording | Template + rules |
| Creative / judgement (tone, wording) | Loose | Principles + 1–2 examples |

## Useful rule patterns
- **Never invent:** "Never invent owners, dates or numbers. Write TBD and list under Needs input."
- **Exactness:** "Keep IDs, names and figures exactly as given."
- **Length:** "≤ N words; cut <section> first if over."
- **Empty sections:** "Write 'None'; never delete a section."
- **Ask vs. assume:** "Ask one question only if the answer changes the content; otherwise use defaults and state them."
- **Conflicts:** "When sources disagree, prefer the most recent and flag the conflict."

## Examples inside skills
- Show 1 short input → output example for format-heavy skills.
- Put long examples in `templates/` or `references/examples.md`.
- Use clearly fake data in examples.
