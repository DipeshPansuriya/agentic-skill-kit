# Conflict Resolution

## Priority order (highest wins)
1. **Safety / compliance rules:** never invent, no secrets, no client-internal leakage
2. **User's explicit preference** (ask if it matters)
3. **Most-used skill's convention**
4. **Most specific / strict rule**
5. **Most recent version**

## Common conflicts
| Conflict | Default resolution |
|---|---|
| Severity scales (P1–P3 vs High/Med/Low) | Pick one; add a mapping line if outputs are consumed by tools |
| Length limits differ | Keep per-part limits as overrides |
| Different report formats | One shared skeleton + per-part sections |
| Tone (formal vs casual) | Tie tone to **audience**, not to the part |
| Naming (tickets, IDs) | Keep exactly as source data; don't normalise |
| Ask vs assume behaviour | Shared rule: ask only when the answer changes content |
| Overlapping scripts | Keep the more general one; test both call sites |

## Recording decisions
Log every conflict in the merge report:
`<Conflict> | Skill A said … | Skill B said … | Decision … | Reason …`
