---
name: sop-writer
description: Turn rough steps or screenshot notes into a Standard Operating Procedure with roles, numbered steps and expected results, troubleshooting and version history. Use when the user asks to write an SOP, work instruction or step-by-step procedure.
---

# SOP Writer

## Inputs
- Rough steps, bullet lists, or a narrated walkthrough
- Screenshot descriptions ("screen 3: Booking tab, click Save")
- Existing SOP to update (keep its version history)
- Optional: role names, system name and version, error messages seen

## Defaults (state them in the output if used)
| Setting | Default | Options |
|---|---|---|
| Reader | New operator, knows the domain, not the screen | Operator · Supervisor · IT support |
| Detail level | One UI action per step | Condensed (expert) · Detailed (trainee) |
| SOP ID / version | "SOP-TBD", v0.1 Draft | As given |
| Owner / approver | TBD | As given |

Ask **one** question only if the system or the role performing the steps is unknown and changes the steps. Otherwise use defaults and state them.

## Steps
1. Read all input; list systems, screens, fields, buttons, roles and error messages exactly as named.
2. Put steps in execution order; split any step with two actions; merge pure duplicates.
3. For each step write: action (imperative verb + UI element in **bold**), expected result, and a screenshot reference if one was described.
4. Mark decision points ("If X, go to step n") and gaps in the flow ("step missing between 4 and 5?") as Needs input.
5. Collect prerequisites (access, data, documents, cut-off times) and exceptions (errors, rejections, timeouts).
6. Fill `templates/sop-template.md`; follow the writing rules in `references/sop-style.md`.
7. For an update, bump the version and add a version-history row describing what changed.
8. Run the self-check and fix before returning.

## Format
Use `templates/sop-template.md`: header table, 1 Purpose, 2 Scope, 3 Roles, 4 Prerequisites, 5 Procedure (numbered table: Step · Action · Expected result · Screenshot), 6 Exceptions & troubleshooting, 7 Related documents, 8 Version history.

## Rules
- **Branding only on request:** use plain, neutral formatting by default. Apply a company or brand design skill (colours, fonts, logo, templates) only when the user names that skill or brand in the request; never pick one automatically.
- Never invent screens, fields, buttons, menu paths, error codes, timings or approvals. Use "TBD" and list under Needs input.
- Keep system names, field labels, message types (FWB, FFM) and IDs exactly as given, including capitalisation.
- One action per step; start with a verb ("Click", "Enter", "Select", "Verify").
- Every step has an expected result; if unknown, write "TBD (confirm)".
- Use role names, not person names, in steps.
- Safety, customs or DG (dangerous goods) checks stay as separate, bold steps; never merge or drop them.
- Steps ≤ 25 per SOP; if more, split into sub-procedures (5.1, 5.2).
- Empty section: write "None". Never delete a section.

## Self-check
- [ ] Every input step appears once, in order
- [ ] Each step: one action, a verb, an expected result
- [ ] No invented UI elements, codes or approvals
- [ ] Decision points and flow gaps flagged
- [ ] Roles, prerequisites and exceptions filled or "None"
- [ ] Version history row present (v0.1 Draft if new)

## Output
Return the SOP, then an **"Assumptions & Needs input"** block (defaults used, TBDs, flow gaps, screens to capture) outside the SOP.

Benchmark after edits with `evals/test-cases.md`.
