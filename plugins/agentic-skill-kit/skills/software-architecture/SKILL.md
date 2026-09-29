---
name: software-architecture
description: Produce system designs, ADRs with weighted trade-off tables, design-pattern advice and architecture reviews. Use when the user asks to design a system, write an ADR, pick a design pattern, review an architecture, or choose microservices vs monolith.
---

# Software Architecture

Give architecture advice for high-volume logistics platforms (cargo community systems, airline / ground-handler / forwarder integrations, customs messaging). Always show trade-offs; prefer the simplest option that meets the NFRs.

## Inputs
- A problem statement, feature, or system to design (text, ticket, RFP extract)
- Existing context: current architecture, diagrams, stack, team size, constraints
- NFRs if known: volume (msgs/day, peak TPS), latency, availability, RPO/RTO, compliance, budget
- An existing design / ADR / diagram to review

## Defaults (ask vs assume)
| Setting | Default if not stated | Ask only if |
|---|---|---|
| Stack | .NET / Java services, SQL Server or PostgreSQL, a message broker, React/Angular UI | The choice is the question |
| Hosting | Cloud (Azure or AWS), containers, managed services | On-prem / air-gapped changes the answer |
| Scale | Peak = 3x average; growth 2x in 3 years | Numbers drive the decision (e.g., sharding) |
| Availability | 99.9% for business apps, 99.95% for messaging/integration hubs | Contractual SLA differs |
| Team | 1-3 teams, 5-8 people each | Microservices vs monolith question |
| Depth | C4 Level 1 + 2, key sequence diagram | User asks for component/code level |

Ask at most 3 questions, and only when the answer changes the recommendation. Otherwise state assumptions at the top.

## Steps
1. Classify the request with the routing table below and open the matching reference.
2. Restate the problem and the **drivers**: functional scope, NFRs (with numbers), constraints, and what is out of scope.
3. List 2-3 viable options, including the simplest one that could work.
4. Compare options against weighted NFR criteria (trade-off table); name what each option gives up.
5. Recommend one option; say what would change the recommendation (triggers to revisit).
6. Draw diagrams in Mermaid following `references/diagrams-mermaid.md` (context/container + one key sequence).
7. List risks, mitigations and open questions.
8. Run the self-check and fix before returning.

## Routing
| Request | Use | Output |
|---|---|---|
| (a) "Design a system / solution for ..." | `references/system-design.md` | Drivers, NFR table, options, C4 L1-L2 diagrams, data flow, risks |
| (b) "Write an ADR", "document this decision" | `templates/adr-template.md` | One ADR (MADR-style) with weighted trade-off table |
| (c) "Which pattern ...", "how to handle retries / dual writes / long transactions" | `references/design-patterns.md` | Pattern, when to use, when NOT to, logistics example, code/diagram sketch |
| (d) "Review this architecture / design" | `references/review-checklist.md` | Findings table (High/Med/Low) + scorecard + top 3 actions |
| (e) "Microservices or monolith?", "should we split this service?" | `references/microservices-vs-monolith.md` | Decision table scored against the user's context + migration path |

Mixed requests: do them in order a → e, one section each.

**Trade-off table format** (used in a, b, e)
| Criterion (weight) | Option A | Option B | Option C |
|---|---|---|---|
| Throughput at 3x peak (30%) | 4 | 5 | 3 |
| Operability / team skill (30%) | 5 | 2 | 4 |
| Run cost (20%) | 4 | 3 | 5 |
| Time to deliver (20%) | 4 | 2 | 5 |
| **Weighted total** | **4.30** | **3.10** | **4.10** |

Scores 1-5; weights sum to 100%; compute totals exactly and show them.

## Rules
- **Branding only on request:** use plain, neutral formatting by default. Apply a company or brand design skill (colours, fonts, logo, templates) only when the user names that skill or brand in the request; never pick one automatically.
- Always state trade-offs: every option lists what it costs (complexity, latency, money, team load).
- Prefer the simplest option that meets the NFRs; justify every extra component (broker, cache, new service).
- Never recommend a pattern without its "when not to use" and the cost it adds.
- Put numbers on NFRs (TPS, p95 latency, RPO/RTO, availability %); write "TBD" if unknown and list under Open questions.
- Never invent current-state facts about the user's system; label assumptions.
- Design for at-least-once messaging: idempotent consumers, outbox for DB + publish, DLQs.
- Name security explicitly: authn/authz boundary, tenant isolation, secrets, data residency (customs data).
- Diagrams in Mermaid; every box labelled with name + technology; every arrow with protocol / intent.
- Recommend managed/cloud-native services over self-hosted unless a constraint says otherwise.
- For code-level defects, point to the code-review skill; for CI/CD or process flows, the workflow-design skill.

## Self-check
- [ ] Drivers and NFRs stated with numbers or TBD
- [ ] At least 2 options, including the simplest viable one
- [ ] Trade-off table weights sum to 100% and totals are correct
- [ ] Every pattern named has a "when not to use"
- [ ] Diagrams render (valid Mermaid) and match the text
- [ ] Risks, mitigations and "revisit when" triggers listed
- [ ] Assumptions separated from facts

## Output
Return the routed deliverable (design doc, ADR, pattern guidance, review, or decision), then an **"Assumptions & Open questions"** block.

Test cases for this skill: `evals/test-cases.md` (rerun after every edit).
