# Answering Guide

## Compliance labels
| Label | Use when | Answer must include |
|---|---|---|
| ✅ Yes | A filled bank entry fully meets the requirement, out of the box or by configuration | Fact + how (standard / configuration) |
| 🟡 Partial | Bank entry meets part; or needs customisation, workaround or third party | What is met + what is not + how the gap can be covered (only if the bank says) |
| 🔵 Roadmap | Bank lists it as roadmap | "Planned" + timeline only if the bank gives one |
| ❌ No | Bank explicitly says not supported | Short, neutral statement; alternative only if in the bank |
| ⚪ Needs input | No filled bank entry, or entry is TO FILL | Nothing factual; gap-log row |

Never upgrade a label to look better (Partial is not Yes; Roadmap is not Partial).

## Length tiers
| Tier | Use for | Length |
|---|---|---|
| S | Yes/No grids, compliance matrices, short-answer cells | Label + ≤ 25 words |
| M | Standard functional or security questions (default when no limit) | Label + 40–80 words |
| L | "Describe your approach / architecture / process" | Label + 120–200 words, bullets allowed |

The client's word or character limit always wins; cut explanation before facts.

## Topic routing
| Topic | Typical keywords | Bank section |
|---|---|---|
| Security | encryption, MFA, SSO, pen test, ISO 27001, SOC 2, vulnerability | A |
| Hosting & continuity | cloud, data residency, DR, RPO, RTO, backup, uptime | B |
| Integration | API, EDI, Cargo-IMP, Cargo-XML, FWB, FFM, customs interface | C |
| Functional | booking, AWB, ULD, warehouse, e-DO, billing | D |
| Support & SLA | support hours, severity, response time, escalation | E |
| Company & commercial | years, offices, customers, licensing, insurance | F |

## Consistency
- Same question asked twice (different wording): same label, same facts.
- If two bank entries disagree, use neither: label Needs input and log the conflict.
