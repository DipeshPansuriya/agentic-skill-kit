# How to Combine Multiple Skills into One

Merging related skills gives you **one set of shared rules**, **one consistent output style** and **smooth multi-step requests**, such as "review this, then check it's ready to deploy".

---

## 1. Should you merge? (decide first)

| ✅ Merge when… | ❌ Keep separate when… |
|---|---|
| The skills cover the same domain (e.g. all tech/dev workflows) | The topics are unrelated (e.g. SQL tuning + HR emails) |
| They share rules, formats or terminology | Each has its own completely different style |
| You often use them together in one request | You always use them alone |
| Maintaining them separately means repeated edits | The merged description would become vague |

**Rule of thumb:** if you can't write one clear description sentence covering all of them, don't merge.

---

## 2. Structure of a merged skill

```
tech-toolkit/
├── SKILL.md               ← short: triggers + routing + shared rules
└── references/
    ├── api-testing.md     ← full content of old skill 1
    ├── code-review.md     ← full content of old skill 2
    └── deploy-check.md    ← full content of old skill 3
```

Keep `SKILL.md` short. Claude reads a reference file **only when** the request needs it, so the merged skill stays fast.

---

## 3. Step-by-step

### Step 1: Inventory the skills
For each skill, list its **description** (triggers), its **steps**, its **format** and its **rules**.

### Step 2: Find the overlap
- Rules repeated in several skills go into **Shared rules**.
- Rules that conflict need one decision now. For example, severity scales "P1–P3" vs "High/Med/Low": pick one.
- Everything unique to one skill stays in that skill's reference file.

### Step 3: Write one combined description
Include **every** task and its trigger phrases.

```
Team tech workflows: API testing, code review, and pre-deploy checks.
Use when the user asks to test an API/endpoint, review code or a PR,
or check a release before deployment.
```

### Step 4: Write the routing section
Tell Claude which file to read for which request, and in what order when several apply.

### Step 5: Move each old skill into `references/`
Remove the rules you moved to Shared rules. Keep the steps and format specific to that task.

### Step 6: Benchmark before replacing
Compare the merged skill against the separate skills (see **03-how-to-benchmark-a-skill.md**). Only retire the old skills if the merged one scores equal or better.

---

## 4. Template for the merged SKILL.md

```markdown
---
name: tech-toolkit
description: Team tech workflows: API testing, code review, and pre-deploy checks. Use when the user asks to test an API, review code/PRs, or check a release before deploy.
---

# Tech Toolkit

## Which part to use
| Request is about… | Read |
|---|---|
| Testing an API / endpoint | references/api-testing.md |
| Reviewing code or a PR | references/code-review.md |
| Checking a release before deploy | references/deploy-check.md |

If more than one applies, do them in this order: **review → test → deploy check**, and produce one combined report.

## Shared rules (apply to every part)
- Severity labels: **High / Med / Low** only.
- Report format: Summary → Findings table (Item | Severity | Fix) → Next steps.
- Never change production config or secrets without asking.
- Quote file names, endpoints and error messages exactly.
- If information is missing, list it under "Needs input". Don't guess.
```

---

## 5. Checklist

- [ ] One clear description covering every task + its trigger phrases
- [ ] Routing table maps each request type to one reference file
- [ ] Multi-task order defined
- [ ] Duplicate rules moved to Shared rules; conflicts resolved
- [ ] Each reference file works on its own
- [ ] Benchmarked against the separate skills before switching
- [ ] Old skills disabled after switching, so two skills don't compete for the same request

## 6. Pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| Description too broad | Triggers on general questions | Add specific "Use when…" phrases |
| Description missing a task | That task no longer triggers | List every task explicitly |
| Everything pasted into SKILL.md | Slow, loads irrelevant content | Move details to `references/` |
| Old + new skills both active | Wrong one triggers | Disable the old ones after switching |
| Built-in/plugin skills merged "in place" | Can't edit them | Copy content into a **new** skill with its own name |
