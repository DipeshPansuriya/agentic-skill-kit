# RCA Methods & Blameless Language

## 5 Whys
- Start from the customer-visible symptom, not the technical failure.
- Each "Why" must be supported by a fact in the input; otherwise mark it **Suspected**.
- Stop when the answer is a process, tooling, design, or monitoring gap you can act on. Usually 3–6 levels.
- Branch if two causes are both necessary (write Why 3a / 3b).

| Level | Question | Answer (evidence) |
|---|---|---|
| Symptom | What did the customer see? | |
| Why 1 | Why did that happen? | |
| Why 2 … 5 | | |
| Root cause | Systemic gap | |

## Contributing factors (check each)
| Category | Ask |
|---|---|
| Change | Deploy, config, cert, partner-side change in the window? |
| Monitoring | Did an alert exist? Did it fire? Was it routed? |
| Capacity | Peak volume (bank season, flight wave, month-end)? |
| Dependency | Airline host, customs gateway, network/ISP, cloud provider? |
| Process | Runbook missing/outdated? Handover gap? Approval skipped? |
| Testing | Scenario not covered in UAT / regression? |
| Data | Bad master data, duplicate AWB, malformed message? |

## Blameless rewrites
| Don't write | Write |
|---|---|
| "Amit deployed without testing" | "The deploy pipeline allowed release without the regression gate" |
| "Support ignored the alert" | "The alert went to a shared inbox with no paging" |
| "Human error" | Name the missing guardrail |

## Audience variants
| Variant | Change from internal |
|---|---|
| **Internal** (default) | Full template, hosts, ticket IDs, contributing factors |
| **Client / airline / authority** | Plain-language summary, impact on *their* shipments, customer-facing timeline (IST or their local zone), preventive actions without internal host names or owner names; no internal tooling details; no blame of partners |
| **Leadership** | Summary + impact + severity + TTD/TTR + top 3 actions, ≤ 150 words |
