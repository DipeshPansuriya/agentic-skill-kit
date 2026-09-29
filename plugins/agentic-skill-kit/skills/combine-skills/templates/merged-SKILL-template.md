---
name: <merged-skill-name>
description: <Domain> workflows: <task A>, <task B>, and <task C>. Use when the user asks to <A triggers>, <B triggers>, or <C triggers>.
---

# <Merged Skill Title>

## Which part to use
| Request is about… | Read |
|---|---|
| <Task A> | references/<a>.md |
| <Task B> | references/<b>.md |
| <Task C> | references/<c>.md |
| None clearly match | Ask one question: which of A / B / C? |

## Multi-task order
If more than one applies: <A> → <B> → <C>. Produce one combined output.

## Shared rules (apply to every part)
- <Severity / label scale>
- <Shared output skeleton>
- Never invent data; use "TBD" and list under Needs input.
- Keep IDs, names and figures exactly as given.
- <Safety / compliance rule>

## Part overrides
- <Part B>: <rule that differs from shared, and why>

## Combined output format
1. Summary
2. <Per-part sections>
3. Overall verdict / next steps
4. Assumptions & Needs input

## Self-check
- [ ] Correct part(s) loaded
- [ ] Shared rules applied
- [ ] Nothing invented
