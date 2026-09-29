# How to Create a Skill

A **skill** is a saved set of instructions Claude follows the same way every time. You write it once. After that, Claude loads it whenever a request matches.

---

## 1. Anatomy of a skill

```
my-skill/
├── SKILL.md          ← required: frontmatter + instructions
├── references/       ← optional: longer docs loaded only when needed
├── templates/        ← optional: output templates, examples
└── scripts/          ← optional: code the skill can run
```

`SKILL.md` has two parts:

| Part | What it does | Loaded when |
|---|---|---|
| **Frontmatter** (`name`, `description`) | Tells Claude *when* to use the skill | Always (short, always visible) |
| **Body** (steps, format, rules) | Tells Claude *how* to do the task | Only when the skill triggers |

---

## 2. Step-by-step

### Step 1: Pick one repeatable task
Good candidates are tasks you do weekly, where the output should look the same every time.
Examples: weekly status report, meeting notes to action items, shipment exception summary.

### Step 2: Collect 1–3 real examples
Gather the **input** you usually start with, and an **output** you were happy with if you have one.

### Step 3: Write the description (the most important line)
- Say **what** the skill does and **when** to use it.
- Include the words you actually type, such as "status report", "weekly update" or "summarize my notes".
- Keep it under ~200 characters.

| ❌ Weak | ✅ Strong |
|---|---|
| `Helps with reports.` | `Turn weekly ops notes into a one-page status report for management. Use when the user asks for a weekly report, status update, or ops summary.` |

### Step 4: Write the body: Steps → Format → Rules
- **Steps:** the process, in order. End with a self-check step.
- **Format:** the exact output structure: sections, order, tables.
- **Rules:** edge cases and "never do" items, such as missing data, length limits and tone.

### Step 5: Test on a real example
Run the skill on one real input and compare the output with what you would have written yourself. Then fix the steps or rules.

### Step 6: Save it
Ask Claude to save the skill. You'll get a review card to approve. Rerun your test after any edit.

---

## 3. Template (copy this)

```markdown
---
name: weekly-status-report
description: Turn rough weekly notes into a one-page status report. Use when the user asks for a weekly report, status update, or summary for management.
---

# Weekly Status Report

## Steps
1. Read all input once before writing.
2. Sort each item into: Done, In progress, Blocked, Next week.
3. Pull out owners, dates, and numbers exactly as written.
4. Remove duplicates and chit-chat.
5. Write the report in the format below.
6. Self-check: nothing important missing, nothing invented.

## Format
**Title:** Team + week (e.g. "Ops Weekly, W39 2026")
**TL;DR:** 2 sentences max
**Done:** bullets
**In progress:** table: Item | Owner | ETA
**Blocked:** bullets with what's needed to unblock
**Next week:** bullets

## Rules
- One page (~300 words). Trim "Done" first if over.
- Never invent owners or dates. Write "TBD".
- Keep IDs, AWB numbers, and figures exactly as given.
- Empty section → write "None" (don't delete it).
```

---

## 4. Quality checklist

- [ ] Description names the task **and** the trigger phrases
- [ ] Steps are numbered and end with a self-check
- [ ] Format is exact enough that two runs look the same
- [ ] Rules cover missing data, length, and "never invent"
- [ ] Tested on at least one real example
- [ ] Body is under ~500 lines (move long material to `references/`)

## 5. Common mistakes

| Mistake | Fix |
|---|---|
| Vague description, so the skill never triggers | Add the real phrases you type |
| Too broad, so it triggers on unrelated requests | Narrow the "Use when…" clause |
| Rules buried in paragraphs | Use short bullet rules |
| No example tested | Always test on real input before saving |
| One giant file | Split details into `references/*.md` |
