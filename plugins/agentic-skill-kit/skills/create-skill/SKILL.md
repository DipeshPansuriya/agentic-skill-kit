---
name: create-skill
description: Build a validated skill package (SKILL.md, references, templates, scripts, evals) for a repeatable work task using the L1-L3 kit method. Use when the user asks to create a skill, turn a weekly task into a skill, or scaffold a SKILL.md.
disable-model-invocation: true
---

# Create a Skill (Advanced)

Turn a task the user repeats into a tested skill package. Work **with** the user: draft → test on real input → refine → package.

## Phase 1: Discover (ask, don't assume)
Collect these, asking at most 3 questions at a time:
1. **Task:** what is repeated, how often, by whom.
2. **Real input:** 1–3 actual examples of what the user starts with.
3. **Good output:** a past result they liked, or what "done" looks like.
4. **Audience & channel:** who reads the output, and where it goes.
5. **Hard rules:** things that must never happen (invented data, wrong tone, leaking internal info).
6. **Trigger phrases:** the words the user actually types when asking for this.

If the user can't provide a real example, build a realistic synthetic one and label it as synthetic.

## Phase 2: Design
1. Choose the **level** with `references/anatomy.md`:
   - **L1 single file:** short task, one format.
   - **L2 (adds reference and template folders):** variants (audiences, channels), long rules.
   - **L3 (adds script and eval folders):** exact calculations, file parsing, or needs regular benchmarking.
   Start at the lowest level that works. Add folders only when there's a reason.
2. Write the **description** using `references/description-writing.md`.
3. Write the body from `templates/SKILL-template.md` as **Inputs → Steps → Format → Rules → Self-check → Output**, using the patterns in `references/patterns.md`.
4. Anything longer than ~40 lines that is only needed sometimes goes to `references/`.
5. Anything that must be exact (dates, math, parsing, validation) goes to `scripts/`.

## Phase 3: Scaffold & validate
```bash
python scripts/scaffold_skill.py <skill-name> --level 3 --out <dir>
python scripts/validate_skill.py <dir>/<skill-name>
```
Fix every ERROR. Review every WARN.

## Phase 4: Test with the user
1. Run the skill on the user's **real** example.
2. Show the output next to the user's "good output" (if provided).
3. Score it with the 5-point checklist in `templates/evals-template.md`.
4. Ask: "What would you change before sending this?" Each answer becomes a rule or format fix.
5. Repeat until the user says it's ready (usually 2–3 rounds).

## Phase 5: Harden
1. Write `evals/test-cases.md` from `templates/evals-template.md`: ≥ 10 cases covering single-task, near-miss (should NOT trigger), edge cases, and consistency.
2. Add one edge case for every problem found in Phase 4.
3. Re-run `validate_skill.py`.

## Phase 6: Package & save
- Offer to save the skill in the user's account (review card), and/or zip the folder with `SKILL.md` at the folder root.
- Report: level chosen and why, files created, test score, known limitations.

## Rules
- Never save a skill that hasn't been run on at least one real (or clearly labelled synthetic) input.
- Description ≤ 1024 chars (aim ≤ 250), must say **what** + **when**.
- `name`: kebab-case, ≤ 64 chars, no "claude"/"anthropic".
- SKILL.md body ≤ 500 lines; move detail to `references/`.
- Every file referenced in SKILL.md must exist (the validator checks this).
- Rules are short imperative bullets, not paragraphs.
- Every skill ends with a **self-check** step and a "never invent" rule when data is involved.
- Don't add scripts for things the model does reliably in prose; do add them for exactness.

## Self-check before handing over
- [ ] Validator passes with 0 errors
- [ ] Tested on real input; user approved output
- [ ] Description includes the user's own trigger words
- [ ] Near-miss cases listed in evals
- [ ] Level justified (no unused folders)
