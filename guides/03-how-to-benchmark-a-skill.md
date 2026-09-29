# How to Benchmark a Skill

A benchmark shows whether a skill (or a merged skill) is **actually better**. You run the same real requests through each version and score the results the same way.

Use it to:
- check that a new skill is better than having no skill
- decide whether a merged skill should replace several separate skills
- confirm an edit didn't break anything (regression check)

---

## 1. Build the test set (15–20 requests)

Use **real requests** you would actually type. Mix four kinds:

| Type | Share | Example | What it tests |
|---|---|---|---|
| Single-task | ~40% | "Review this PR" | Right skill/part triggers |
| Multi-task | ~20% | "Review this, then check it's deploy-ready" | Combining works |
| Near-miss (should NOT trigger) | ~20% | "What is a REST API?" | Skill stays quiet |
| Edge case | ~20% | Missing owner, huge input, messy notes | Rules still hold |

For each request, write down the **expected result** before you run it: should the skill trigger, which part should it use, and what must the output contain.

---

## 2. What to measure

| # | Metric | How to score | Target |
|---|---|---|---|
| 1 | **Trigger accuracy** | % of requests where the skill triggered correctly (or correctly stayed quiet) | ≥ 90% |
| 2 | **Routing accuracy** *(merged skills)* | % where the right reference file was used | 100% on single-task |
| 3 | **Output quality** | Checklist score per output (see below), 0–5 | ≥ 4 average |
| 4 | **Consistency** | Run 3 requests 3× each; same structure every time? | 3/3 match |
| 5 | **Cost & speed** | Tokens + seconds per request | Not much higher than baseline |

### Output quality checklist (1 point each)
1. Follows the required format / section order
2. All key facts from the input are present
3. Nothing invented (owners, dates, numbers)
4. Rules respected (length, tone, "TBD" for missing data)
5. Usable as-is, without manual edits

---

## 3. Procedure

1. **Freeze the versions.** Label them, e.g. **A = separate skills** (or no skill) and **B = merged skill**.
2. **Run every test request** through A and B in fresh sessions.
3. **Score each output** with the checklist. Where possible, have someone who doesn't know which version is which score them (blind review).
4. **Repeat 3 requests 3×** to check consistency.
5. **Fill in the scorecard** below.
6. **Apply the decision rule.**
7. **Save the test set.** Rerun it after every future edit.

> Tip: Claude's **skill-creator** skill can automate most of this. It can run the test prompts with and without the skill, repeat runs to check variance, test trigger accuracy, and show results side by side. Ask: *"Benchmark my skill X against Y using skill-creator."*

---

## 4. Scorecard template

| # | Request | Type | Expected | A: triggered? | A: quality (0–5) | B: triggered? | B: quality (0–5) | Notes |
|---|---|---|---|---|---|---|---|---|
| 1 | | Single | | | | | | |
| 2 | | Multi | | | | | | |
| 3 | | Near-miss | Should NOT trigger | | | | | |
| 4 | | Edge | | | | | | |
| … | | | | | | | | |

### Summary

| Metric | A | B | Winner |
|---|---|---|---|
| Trigger accuracy | % | % | |
| Routing accuracy | – | % | |
| Avg output quality | /5 | /5 | |
| Consistency (3×3) | /9 | /9 | |
| Avg tokens / time | | | |

---

## 5. Decision rule

| Result | Decision |
|---|---|
| B ≥ A on triggering **and** quality, and better on multi-task | ✅ **Switch to B** and disable the old skills |
| B triggers on near-misses (false positives) | 🔧 **Narrow B's description**, then retest |
| B misses a task (false negatives) | 🔧 **Add that task's phrases** to the description, then retest |
| B uses the wrong part / quality drops on single tasks | ❌ **Keep A.** The skills probably don't belong together |
| Scores are equal and nothing else improves | ⚖️ Keep whichever is **easier to maintain** |

---

## 6. Regression check (after any edit)

- [ ] Rerun the full saved test set
- [ ] No metric dropped compared with the last run
- [ ] New edge case added for the problem that caused the edit
- [ ] Scorecard saved with date + version label
