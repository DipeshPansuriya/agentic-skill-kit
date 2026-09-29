# Routing Patterns

## 1. Table router (default)
Use when parts map cleanly to request types.
```markdown
| Request is about… | Read |
|---|---|
| Testing an API | references/api-testing.md |
| Reviewing a PR | references/code-review.md |
```

## 2. Pipeline router
Use when parts are often chained.
```markdown
If several apply, run in order: review → test → deploy-check.
Produce ONE combined report: Summary → per-stage findings → overall verdict.
Stop the pipeline if a stage returns a High-severity blocker; report why.
```

## 3. Input-type router
Use when the *input* decides the path.
```markdown
- CSV/Excel attached → references/tabular.md
- Code diff pasted → references/code.md
- Free text only → references/notes.md
```

## 4. Audience router
Use when the same task has different outputs per reader.
```markdown
Audience = Manager | Leadership | Client → references/audiences.md#<audience>
```

## Routing rules
- Every request type maps to exactly one entry.
- Include a **fallback**: "If none match, ask one question: which of <parts>?"
- Add cross-routing near-misses to evals (request for A must not load B).
