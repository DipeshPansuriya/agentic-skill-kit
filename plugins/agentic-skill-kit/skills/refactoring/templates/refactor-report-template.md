# Refactor Report: {component or file}

**Scope:** {files / procs touched; public contract kept: yes/no (what changed and who approved)}
**Mode:** {tidy | restructure | minimize | legacy}  ·  **Ponytail:** {used at full / lite / ultra | not installed (fallback ladder) | off}
**Stack:** {e.g. .NET 8 / C# 12, repo style: 4-space, file-scoped namespaces}

## Safety net
| Kind | Where | Result before | Result after |
|---|---|---|---|
| Existing tests | {project / command} | {n passed} | {n passed} |
| Characterization tests added | {file} | {n cases, pinned} | {n passed} |
| SQL result-equivalence | {query / script} | - | {0 rows only_old / 0 rows only_new; counts equal} |

{If waived: **Safety net: waived by user.** Risk: behaviour changes would go unnoticed; changes limited to tidy steps.}

## Steps applied
| # | Refactoring | Where | Why | Tests green? |
|---|---|---|---|---|
| 1 | {Guard Clauses} | {calc_charge} | {nesting 4 → 1} | {yes} |
| 2 | {Replace Magic Number with Constant} | {…} | {…} | {yes} |

## Metrics (`scripts/code_metrics.py --compare`)
| Metric | Before | After | Delta |
|---|---|---|---|
| Code lines | | | |
| Functions | | | |
| Max function lines | | | |
| Max complexity | | | |
| Max nesting | | | |
| Max params | | | |
| Duplicate blocks | | | |
| SQL cursors | | | |
| Flagged functions | | | |

## Behaviour check
- Same outputs for: {inputs / cases}
- Same errors for: {invalid inputs}
- Deliberately preserved quirks: {e.g. `== True` kept; NULL status excluded}
- Behaviour changes: **None** {or list each one, marked "approved by user" or "needs approval"}

## Risks / follow-ups
- {Not done here, handed off: perf → code-performance / sql-performance-tuning; security → security-review-fix}
- {API changes suggested but not made (e.g. Introduce Parameter Object for 10-param method)}
- {Remaining hotspots from the metrics report}
