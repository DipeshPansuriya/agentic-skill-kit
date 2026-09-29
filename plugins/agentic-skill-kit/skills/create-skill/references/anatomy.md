# Skill Anatomy & Levels

```
skill-name/
├── SKILL.md       required: frontmatter (name, description) + body
├── references/    loaded only when SKILL.md points to them
├── templates/     output skeletons, examples
├── scripts/       code for exact / repeatable operations
└── evals/         test cases for benchmarking
```

## How loading works (progressive disclosure)
| Layer | When it's read | Budget |
|---|---|---|
| `name` + `description` | Always, for every request | ~1 short paragraph |
| SKILL.md body | When the description matches | ≤ 500 lines |
| references / templates | When the body says "read X" | No hard limit, keep focused |
| scripts | Executed, not read, when possible | Any size |

This is why the description must be precise, and why the body should point to references instead of containing everything.

## Choosing a level
| Level | Structure | Use when | Example |
|---|---|---|---|
| **L1** | SKILL.md only | One task, one format, < ~150 lines | Notes → one-page summary |
| **L2** | + references/, templates/ | Variants (audience, channel), long rule tables | Status report with 4 audiences |
| **L3** | + scripts/, evals/ | Exact calculations, file parsing, validation, regular benchmarking | Report with week math, CSV input, regression tests |

**Upgrade triggers:**
- SKILL.md > 300 lines → move sections to references (L2)
- Same output drifts between runs → add a template (L2)
- Model makes arithmetic/date/parsing mistakes → add a script (L3)
- Skill is edited often or shared with a team → add evals (L3)
