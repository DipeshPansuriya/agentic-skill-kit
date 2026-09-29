# Severity Rubric (Exploitability × Impact)

Severity = combine the two scores below. Always write a one-line rationale: "Exploitability: X because …; Impact: Y because …".

## Exploitability
| Score | Meaning | Examples |
|---|---|---|
| **E3 Easy** | Unauthenticated or any logged-in user, remote, no special conditions | Public endpoint with SQL concat; leaked AWS key in public repo |
| **E2 Moderate** | Needs a valid account, specific role, user interaction, or internal network | Stored XSS requiring a victim click; IDOR needing a customer login |
| **E1 Hard** | Needs admin/insider access, rare race, or unusual config | Weak hash in an admin-only export; debug flag only in a disabled profile |

## Impact
| Score | Meaning | Examples |
|---|---|---|
| **I3 Severe** | Full data breach, cross-tenant access, RCE, account takeover, financial/customs fraud, safety-relevant data change (e.g. DG declarations, weights) | Deserialization RCE; BOLA across forwarders' shipments |
| **I2 Significant** | Limited data exposure, single-account compromise, integrity of non-critical data, service disruption | PII in logs; reflected XSS; missing rate limit on login |
| **I1 Minor** | Information disclosure with little value, defence-in-depth gap | Missing `Referrer-Policy`; `Server` header version |

## Matrix
| | I3 Severe | I2 Significant | I1 Minor |
|---|---|---|---|
| **E3 Easy** | **Critical** | **High** | Med |
| **E2 Moderate** | **High** | Med | Low |
| **E1 Hard** | Med | Low | Low |

## Adjusters
| Condition | Adjust |
|---|---|
| Real secret exposed (valid credential) | At least **High**; **Critical** if production or cloud admin rights |
| Exploit needs input you cannot trace to an external source | Keep severity, label **Verify**, state what to confirm |
| Strong compensating control verified (WAF rule, network isolation, feature flag off in prod) | −1 level, name the control |
| Regulated data (passport/APIS, payment card, personal data under GDPR/DPDP) | +1 impact level |
| Test-only / dead code not shipped | Low, recommend removal |

## Priority / SLA suggestion
| Severity | Fix target |
|---|---|
| Critical | Immediately (hotfix; rotate secrets same day) |
| High | Current sprint / ≤ 7 days |
| Med | ≤ 30 days |
| Low | Backlog / next touch |

If the team uses CVSS v4.0 or v3.1, map: Critical 9.0-10.0, High 7.0-8.9, Medium 4.0-6.9, Low 0.1-3.9, and include the vector string only when you actually computed it.
