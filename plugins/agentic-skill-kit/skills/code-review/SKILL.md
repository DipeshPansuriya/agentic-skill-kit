---
name: code-review
description: Review code, a pull request or a diff and return a severity-ranked findings table with concrete fixes and a verdict. Use when the user asks to review code, check a PR, audit a diff, look over a change, or find bugs before merge.
---

# Code Review

Review a change like a senior engineer on an air-cargo / logistics platform: find what will break in production, leak data, or slow the system down. Report only what the code proves.

## Inputs
- Pasted code, a file, a diff / patch, or a PR link / branch the user can open
- Optional: PR description, ticket, linked requirements, test output, CI logs
- Optional: focus ("security only", "performance"), team checklist, stack notes

Review the **diff first**, then read surrounding code only as needed to confirm a finding. When several files are given, review them together (cross-file bugs count).

## Defaults (ask vs assume)
| Setting | Default if not stated | Ask only if |
|---|---|---|
| Scope | Changed lines + direct callers/callees | User says "whole repo" and it is large |
| Categories | All 7 (see Format) | Never; narrow only if the user asks |
| Depth | Standard (all High/Med, Low only if cheap to fix) | Never |
| Style nitpicks | Off | Never; on only if user asks |
| Stack | Inferred from file extensions and imports | Mixed or unclear and it changes the checks |

State the defaults you used in one line above the table.

## Steps
1. Read the PR description / ticket (if any) to learn the **intent**; note any mismatch between intent and code.
2. Identify the stack(s) and load the matching section of `references/checklist-by-stack.md`.
3. Walk the diff hunk by hunk against `references/checklist-general.md` (7 categories).
4. For each candidate issue, confirm it in the code: find the exact file and line. If you cannot point to it, drop it or mark **Verify** (see Rules).
5. Assign severity using the table in Format. Merge duplicates (same root cause → one row, list all lines).
6. Write a concrete fix for every High and Med: a code snippet or exact change, not advice.
7. Note missing tests for each High/Med, and whether existing tests cover the change.
8. Decide the verdict from the verdict rules.
9. Run the self-check and fix before returning.

## Format
**Severity**
| Severity | Meaning | Examples |
|---|---|---|
| **High** | Wrong results, data loss/corruption, security hole, outage risk, breaks contract | SQL injection (OWASP A05), missing auth check, double-processing of AWB events, unhandled null on hot path |
| **Med** | Likely bug under realistic load/edge, notable perf or reliability gap, missing tests for risky logic | N+1 query, retry without backoff, swallowed exception, no timeout on HTTP call |
| **Low** | Maintainability / clarity issue with real cost | Duplicated business rule, magic number for a customs code, misleading name |

**Categories:** Correctness · Security (OWASP Top 10:2025) · Performance · Reliability/Error handling · Maintainability · Tests · Observability

**Output skeleton**
```markdown
**Verdict:** Request changes | Approve with comments | Approve  
**Summary:** 2-3 sentences: what the change does, overall quality, the top risk.  
_Defaults: scope = diff + callers; style nitpicks off; stack = .NET 8 / SQL Server._

| # | Sev | Category | File:line | Issue | Why it matters | Fix |
|---|---|---|---|---|---|---|
| 1 | High | Security | `Api/AwbController.cs:42` | Raw SQL concatenates `awbNo` | Injection (OWASP A05); exposes all shipments | Use parameter: `cmd.Parameters.Add("@awb", SqlDbType.VarChar, 12).Value = awbNo;` |
| 2 | Med | Reliability | `Messaging/FwbConsumer.java:88` | **Verify:** handler not idempotent on redelivery | Duplicate FWB may create 2 bookings | Check `messageId` in processed-messages table before insert |

**Tests:** what is covered, what is missing (per High/Med).  
**Good:** 1-3 specific things done well (optional, one line each).  
**Questions for author:** only items that block a verdict.
```

**Verdict rules**
| Condition | Verdict |
|---|---|
| Any High (confirmed) | **Request changes** |
| No High; any Med, or any High marked Verify | **Approve with comments** |
| Only Low or nothing | **Approve** |

No findings: say so, give the verdict "Approve", and list what you checked.

## Rules
- Report only issues you can point to at a file and line. No generic advice.
- Mark anything you cannot fully confirm from the given code as **Verify:** and say what to check.
- Never invent file names, line numbers, APIs or framework behaviour; if lines are not numbered, cite the function/method name.
- No style or formatting nitpicks unless the user asks; linters do that.
- Every High/Med gets a concrete fix (code or exact change). Match the codebase's language and conventions.
- One root cause = one row. Rank rows High → Med → Low, then by blast radius.
- Security first: check authn/authz, input validation, secrets, injection, SSRF, deserialization on every change that touches I/O.
- Treat message handlers (Cargo-IMP / Cargo-XML, queues, webhooks) as at-least-once: check idempotency, ordering and poison-message handling.
- Don't rewrite the author's design in a review; raise design concerns as one Med/Low row, or suggest the software-architecture skill.
- Be direct and neutral: describe the code, not the author.
- Stay a review (findings + verdict). For deep follow-up work, recommend the sibling skill instead of doing it here:
  | Need | Hand off to |
  |---|---|
  | Find and fix all vulnerabilities, rotate secrets | security-review-fix |
  | Measured speed / memory optimization | code-performance |
  | Slow query, execution plan, index tuning | sql-performance-tuning |
  | Large cleanup of messy or long code (incl. ponytail) | refactoring |

## Self-check
- [ ] Every row has a real File:line (or function) that exists in the input
- [ ] Uncertain rows are labelled **Verify**
- [ ] Every High/Med has a concrete fix
- [ ] No style nitpicks (unless asked); no duplicates
- [ ] Security, correctness and tests were each explicitly checked
- [ ] Verdict matches the verdict rules
- [ ] Stack checks from `references/checklist-by-stack.md` applied

## Output
Return the verdict, summary and findings table, then Tests / Good / Questions. End with a one-line **"Not reviewed"** note listing anything out of scope (files not provided, generated code, infra).

Test cases for this skill: `evals/test-cases.md` (rerun after every edit).
