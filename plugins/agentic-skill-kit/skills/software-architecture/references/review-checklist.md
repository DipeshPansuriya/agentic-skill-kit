# Architecture Review Checklist

Output: findings table `| # | Sev | Area | Finding | Evidence (doc/diagram section) | Recommendation |`, a scorecard, then the top 3 actions. Report only what the material shows; mark gaps "Not documented" (Med) rather than assuming.

## Scorecard (1-5 each, with one-line reason)
| Area | 1 = | 5 = |
|---|---|---|
| Fit to requirements & NFRs | NFRs missing | Every NFR has a number and a mechanism |
| Simplicity | Many components without drivers | Every component justified |
| Resilience | Single points of failure, no retries/timeouts | Failure modes designed and tested |
| Security | No authz model | Threat-modelled, least privilege, tenant isolation |
| Data | Shared DB across services, unclear ownership | Clear ownership, consistency model stated |
| Operability | No monitoring/runbooks | SLOs, alerts, IaC, runbooks |
| Evolvability | Tight coupling, no versioning | Versioned contracts, clear seams |
| Cost | Unknown | Estimated and within budget |

## Checks
| Area | Check |
|---|---|
| Requirements | NFRs quantified (TPS, p95, availability, RPO/RTO); peak and growth stated |
| Requirements | Key decisions have ADRs with alternatives |
| Structure | Boundaries follow business capabilities (booking, acceptance, manifest, customs, billing) |
| Structure | No distributed monolith: services that always deploy together or share tables |
| Structure | Sync call chains ≤ 3 hops on user-facing paths |
| Data | Each dataset has one owner; others use APIs/events or read replicas |
| Data | Consistency model explicit per flow (strong vs eventual) and acceptable to business |
| Data | Retention, archival, and audit trail for regulated messages |
| Integration | Partner formats isolated behind an anti-corruption layer; schemas versioned |
| Integration | At-least-once delivery handled: idempotency, ordering key, DLQ + replay tool |
| Integration | DB write + event publish atomic (outbox) |
| Resilience | Timeouts, retries with backoff, circuit breakers on every remote call |
| Resilience | Multi-AZ; DR tested; RPO/RTO achievable with chosen backups/replication |
| Resilience | Backpressure / rate limits for partner bursts (flight banks, month-end) |
| Security | AuthN (OIDC/OAuth2), AuthZ per tenant/party, service-to-service identity (mTLS or managed identity) |
| Security | Secrets in a vault; encryption in transit and at rest; data residency for customs data |
| Security | Threat model (STRIDE) for external interfaces |
| Operability | OpenTelemetry traces with business keys (AWB, flight); SLOs + alerting |
| Operability | IaC; blue-green/canary deploys; rollback path; feature flags |
| Cost | Cost estimate at current and 3x volume; autoscaling limits set |
