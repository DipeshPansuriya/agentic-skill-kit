---
name: refactoring
description: Refactor code or stored procedures into shorter, maintainable code with the same behaviour, tests and before/after metrics. Use when the user asks to refactor, clean up, simplify, shorten, reduce code, fix legacy code or messy SQL, or use ponytail.
---

# Refactoring (code and SQL)

Turn hard-to-maintain code into clean, shorter code that does **exactly** the same thing. Every change is backed by tests or a result-equivalence check, and ends with before/after metrics.

## Inputs
- Code (file, folder, pasted snippet, diff), a stored procedure / function / view, or a repo path
- Optional: goal ("make it readable", "cut it in half"), constraints (keep API, no new deps), existing tests, style guide

## Defaults (state them in one line at the top)
| Setting | Default | Ask only if |
|---|---|---|
| Mode | Picked from the request (table below) | Request fits two modes with different risk (e.g. `minimize` vs `legacy`) |
| Public API | Kept (names, signatures, return types, errors, SQL result shape) | User asks to change it |
| Safety net | Required; write characterization tests if none exist | User explicitly waives it (then flag the risk) |
| Style | The repo's existing style and language version | No code style visible and it changes the output |
| Ponytail | Used in `minimize` if installed, intensity `full` | Not installed: offer install, ask first |

## Pick the mode
| Mode | Use when the user says… | Typical steps | Risk |
|---|---|---|---|
| `tidy` | "clean up", "make readable", small file | Rename, constants, guard clauses, formatting, remove dead code | Low |
| `restructure` | "split this class", "too long", "separate concerns" | Extract method/class, move, introduce parameter object, lookup tables | Medium |
| `minimize` | "shorten", "reduce code", "too much code", "ponytail" | Minimize ladder (Step 5), stdlib/framework idioms, delete YAGNI | Medium |
| `legacy` | "legacy", "no tests", "afraid to touch", "huge file" | Characterization tests, seams, sprout/wrap, strangler | High |

## Route by stack
| Code is… | Read |
|---|---|
| C# / .NET, Java / Spring, Python, TypeScript (React or Angular) | `references/stack-idioms.md` (that stack's section) + `references/smells-catalog.md` |
| T-SQL procs, PL/pgSQL functions, views, long queries | `references/sql-refactoring.md` |
| No tests, legacy, 1,000+ line files, god-procedures | `references/legacy-strategies.md` (first), then the stack file |
| `minimize` mode, or the user mentions Ponytail | `references/ponytail.md` |
| Worked before/after examples | `templates/samples/` (Python, C#, T-SQL, PL/pgSQL) |

## Steps
1. **Understand & scope.** Say what the code does in 2–3 lines, list its public contract (signatures, return values, exceptions, SQL result columns, side effects) and its callers (search the repo). Pick the mode. For repo-wide asks, rank targets with `scripts/code_metrics.py` (and `/ponytail-audit` if installed).
2. **Safety net first.** Run existing tests. If there are none, write characterization tests that pin current behaviour, incl. edge cases (null/empty/boundary/invalid input, exception type and message) — see `references/legacy-strategies.md`. For SQL, prepare the result-equivalence check (`EXCEPT` both ways + row count / checksum) from `references/sql-refactoring.md`. No safety net and no explicit waiver → stop and ask.
3. **Measure before.** `python3 scripts/code_metrics.py path/to/code` (add `--json` for tooling). Note flagged functions: > 40 lines, nesting > 3, params > 4, complexity > 10, SQL cursors, duplicate blocks.
4. **Refactor in small, named steps.** One refactoring per step, tests green after each. Use names from `references/smells-catalog.md`: Extract/Inline Method, Rename, Guard Clauses, Decompose Conditional, Replace Conditional with lookup table or polymorphism, Introduce Parameter Object, Replace Magic Number, Remove Dead Code, Replace Loop with Pipeline / LINQ / streams / comprehension (only if clearer). SQL: CTEs, set-based instead of cursors, remove duplicated subqueries, consistent formatting and naming, split god-procedures, TRY/CATCH and transaction hygiene.
5. **Minimize** (always in `minimize` mode; lightly in the others). Walk the ladder, stop at the first yes:
   1. Does it need to exist? (YAGNI: delete unused code, options, layers)
   2. Does the repo already have it? (reuse)
   3. Does the stdlib / framework do it? (use it)
   4. Otherwise write the minimal clear code.
   If Ponytail is installed, set intensity and run `/ponytail-review` on the diff per `references/ponytail.md`; if it isn't, offer the install commands, **ask before installing**, and continue with the ladder.
6. **Verify.** All tests / equivalence checks pass. Run `python3 scripts/code_metrics.py --compare before_path after_path` (files or folders; keep a copy of the originals). Report lines, functions, max complexity, max nesting before → after.
7. **Report** with `templates/refactor-report-template.md`, then run the self-check.

## Rules
- **Behaviour preservation is non-negotiable.** Same outputs, errors, side effects, SQL result sets (columns, types, NULL handling, row multiplicity). Keep odd behaviour that callers may rely on (e.g. `== True`, culture-sensitive formatting, NULL exclusion) and say so.
- **No refactor without a safety net**, unless the user explicitly waives it; then limit to `tidy` steps and mark the report "Safety net: waived by user" with the risk.
- **One concern per step.** Don't mix refactoring with features, bug fixes, performance or security fixes. Hand off: speed → code-performance; slow queries → sql-performance-tuning; vulnerabilities → security-review-fix; PR verdicts → code-review; new features → backend-engineering / frontend-engineering / database-engineering. Bugs found: list under follow-ups, don't fix silently.
- **Keep public APIs** unless asked. For an API improvement (parameter object, split flag argument), add the new form and keep the old one delegating, or list it as a follow-up.
- **Shorter only if equally or more readable.** No clever one-liners, nested ternaries or golfed comprehensions. Never drop validation, error handling, security checks, logging needed for audit, or accessibility to save lines.
- **Follow the repo's style**, language version and libraries; add no new dependencies in a refactor.
- **Show numbers**: before/after metrics from the script, never estimated by hand.
- **Big files:** plan the split first, move before editing, deliver in checkpoints (see `references/legacy-strategies.md`).
- **Ponytail** is optional and advisory: its suggestions pass the same tests and metrics; never install it without asking.

## Self-check
- [ ] Mode and defaults stated; public contract listed
- [ ] Safety net existed or was written before changes (or waiver recorded with risk)
- [ ] Every step is a named refactoring; no feature, bug, perf or security change mixed in
- [ ] Tests / equivalence check pass after the last step; SQL checked with `EXCEPT` both ways + counts
- [ ] Public API unchanged (or change approved and listed)
- [ ] Metrics before/after from `scripts/code_metrics.py --compare`
- [ ] Result is at least as readable; validation, errors, security, accessibility intact
- [ ] Ponytail: used and reviewed, or missing → asked before install and fell back to the ladder
- [ ] Follow-ups list hand-offs to sibling skills

## Output
1. **Assumptions / defaults** (one line): stack, mode, API kept, Ponytail status.
2. **Refactored code**, one block per file with its path (or a unified diff for small changes).
3. **Tests added** (characterization / equivalence), one block per file, plus the run command.
4. **Report** from `templates/refactor-report-template.md`: steps table, metrics before/after, behaviour check, risks / follow-ups.

Samples (fake data, behaviour-preserving, measured with the script):
| Stack | Before | After | Equivalence |
|---|---|---|---|
| Python | `templates/samples/python_before.py` | `templates/samples/python_after.py` | `templates/samples/check_python_equivalence.py` (33k inputs, 0 mismatches) |
| C# | `templates/samples/csharp_before.cs` | `templates/samples/csharp_after.cs` | Notes in file header (preserved quirks) |
| T-SQL | `templates/samples/tsql_before.sql` | `templates/samples/tsql_after.sql` | Write-proc check in `references/sql-refactoring.md` |
| PL/pgSQL | `templates/samples/plpgsql_before.sql` | `templates/samples/plpgsql_after.sql` | `EXCEPT ALL` both ways, 0 rows (PostgreSQL 16) |

Test cases: `evals/test-cases.md` (rerun after every edit).
