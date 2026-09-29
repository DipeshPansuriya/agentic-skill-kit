# Security Review & Fix Report: {system / repo / PR}

_Scope: {files, services, config, dependencies reviewed} · Stack: {e.g. .NET 8, Angular 18, SQL Server} · Date: {YYYY-MM-DD}_  
_Threat context: {internet-facing? authenticated users? tenants? data classes: customer PII, passport/APIS, payment, customs}_

## 1. Summary
| Critical | High | Med | Low | Verify |
|---|---|---|---|---|
| {0} | {2} | {1} | {1} | {1} |

{2-3 sentences: most serious risk, what was fixed, what remains.}

## 2. Findings
| # | Sev | CWE / OWASP | File:line | Issue | Rationale (exploitability × impact) | Status |
|---|---|---|---|---|---|---|
| 1 | High | CWE-89 / A05:2025 | `{Api/AwbController.cs:42}` | {SQL built from `awb` route value} | {E3 public endpoint × I2 read of all AWBs} | Fixed |
| 2 | Med | CWE-532 / A09:2025 | `{Auth/LoginService.cs:88}` | **Verify:** {password logged on failure} | {E2 log access × I2 credential exposure} | Fixed |

## 3. Fixes (minimal diffs)
### Finding 1: {title}
```diff
- {vulnerable line}
+ {secure line}
```
Why this fixes it: {one line}. Behaviour for valid input: unchanged.

## 4. Tests proving the fixes
| Finding | Test | Asserts |
|---|---|---|
| 1 | `{AwbControllerTests.Get_InjectionPayload_TreatedAsLiteral}` | {`' OR '1'='1` returns 404 / 0 rows; valid AWB still returns 200} |

## 5. Secrets
| Secret (masked) | Location | Action |
|---|---|---|
| `{AKIA****}` | `{config/appsettings.json:12}` | **Rotate** at issuer, moved to {Key Vault}, history purge {optional} |

## 6. Dependencies
| Package | Current | Fixed in | Advisory | Action |
|---|---|---|---|---|
| {Newtonsoft.Json} | {12.0.1} | {13.0.1} | {GHSA-5crp-9r3c-p9vr} | {Upgraded} |

## 7. Residual risk & follow-ups
| Item | Why not fixed now | Owner / next step |
|---|---|---|
| {Add CSP header} | {Needs front-end inline script cleanup} | {TBD} |

## 8. What was checked
{Checklist areas covered, tools/commands run with versions, what was NOT reviewed (e.g. infra, runtime DAST). This report does not certify the system as secure.}
