---
name: karpathy-guidelines
description: "Use on non-trivial code work: ask before assuming, write the minimum, touch only the request, verify with a check. Not for a one-line typo. Complements ponytail; does not replace tests or security."
user-invocable: true
---

# Four coding checks (caution over speed)

This file in DipeshPansuriya/agentic-skill-kit is the whole skill. Do not install a third-party plugin or append a remote CLAUDE.md. Skip on a genuine one-line fix. Pair with `## ponytail-minimal-code` and `## ask-or-act`.

## 1. Think before coding

State assumptions. If several readings exist, list them — do not pick silently. If it is unclear, stop and name the gap (`Needs decision` when spawned).

## 2. Simplicity first

Minimum that solves the ask. No extra features, no single-use abstraction, no unused configurability. If 200 lines could be 50, rewrite. Trust-boundary validation, data-loss handling, security and accessibility stay.

## 3. Surgical changes

Every changed line traces to the request. Do not restyle neighbours, refactor unbroken code, or delete pre-existing dead code (mention it). Do remove orphans **this** change created.

## 4. Goal-driven execution

Turn the ask into a check you can run:

- "Add validation" → tests for invalid inputs, then make them pass
- "Fix the bug" → a test that reproduces it, then green
- "Refactor X" → suite green before and after

Multi-step: `step → verify: check`. Weak "make it work" is not a goal.

Working if: smaller diffs, fewer rewrites, questions before code — not after mistakes.
