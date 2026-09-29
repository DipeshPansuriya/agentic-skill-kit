# General Review Checklist (all stacks)

Walk each hunk through these 7 categories. Each check lists the typical severity if it fails.

## 1. Correctness
| Check | Typical sev |
|---|---|
| Code does what the ticket/PR says; edge cases (empty, null, zero, max, duplicates) handled | High |
| Boundary math: off-by-one, integer overflow, rounding of weights/volumes/charges (use decimal, not float, for money and chargeable weight) | High |
| Time: UTC stored, local time only at display; time zones of origin/destination airports handled; DST-safe | High |
| Concurrency: shared mutable state, race on check-then-act, missing optimistic concurrency (rowversion/ETag) | High |
| Contract changes: API/message schema changes are backward compatible or versioned | High |
| Parsing of external formats (Cargo-IMP, Cargo-XML, EDI, CSV) tolerates optional/unknown fields and rejects malformed ones explicitly | Med |

## 2. Security (OWASP Top 10:2025)
| OWASP | Check | Typical sev |
|---|---|---|
| A01 Broken Access Control | Every endpoint enforces authz; tenant/party filter (airline, GHA, forwarder) applied server-side; no IDOR via AWB/booking IDs; user-supplied URLs allow-listed (SSRF now sits here) | High |
| A02 Security Misconfiguration | No debug/verbose errors to clients; CORS not `*` with credentials; secure headers; no default creds | Med |
| A03 Software Supply Chain Failures | New dependencies pinned, maintained, no known CVEs; lockfile updated; CI actions pinned by SHA | Med |
| A04 Cryptographic Failures | TLS only; no custom crypto; passwords hashed (Argon2id/bcrypt/PBKDF2); PII not stored/logged in clear | High |
| A05 Injection | Parameterized SQL/ORM; no string-built queries, shell commands, XPath; HTML output encoded | High |
| A06 Insecure Design | Rate limits, business-rule abuse (e.g., re-rating a booking), missing server-side validation | Med |
| A07 Authentication Failures | Token validation (issuer, audience, expiry, signature); no auth bypass on new routes | High |
| A08 Software or Data Integrity Failures | No unsafe deserialization of untrusted data; webhook/message signatures verified | High |
| A09 Security Logging and Alerting Failures | Auth failures / permission denials logged without secrets and alertable | Med |
| A10 Mishandling of Exceptional Conditions | Errors fail closed (deny on exception); no stack traces to clients; no half-applied state | Med |
| Secrets | No keys, connection strings, tokens in code/config committed; use a vault / managed identity | High |

## 3. Performance
| Check | Typical sev |
|---|---|
| N+1 queries / queries inside loops | Med |
| Unbounded result sets: missing paging/limit on lists (shipments, events) | Med |
| Missing index for new WHERE/JOIN/ORDER BY columns (ask for query plan if unsure: **Verify**) | Med |
| Blocking I/O on async paths; sync-over-async | Med |
| Large objects loaded into memory (whole file, whole table) where streaming fits | Med |
| Chatty remote calls that can be batched; missing caching for static reference data (airports, carriers, ULD types) | Low |

## 4. Reliability / Error handling
| Check | Typical sev |
|---|---|
| Exceptions not swallowed; errors propagated or handled with a clear outcome | Med |
| Every outbound call (HTTP, DB, queue) has a timeout | Med |
| Retries only on transient errors, with exponential backoff + jitter and a cap | Med |
| Message consumers idempotent (dedupe by message ID / business key) and poison messages go to a DLQ | High |
| DB write + message publish is atomic (transactional outbox) or explicitly tolerant of partial failure | High |
| Resources disposed/closed (connections, streams, HTTP clients reused properly) | Med |

## 5. Maintainability
| Check | Typical sev |
|---|---|
| Business rules not duplicated across layers/services | Low |
| Magic values (status codes, SHC codes, customs codes) are named constants/enums | Low |
| Functions do one thing; deep nesting reduced with guard clauses | Low |
| Dead code, commented-out code, TODOs without ticket | Low |
| Public API/contract changes documented | Low |

## 6. Tests
| Check | Typical sev |
|---|---|
| New logic has unit tests covering happy path + at least one failure and one edge case | Med |
| Bug fix includes a regression test that fails without the fix | Med |
| Tests assert behaviour, not implementation; no sleeps for timing | Low |
| Integration/contract tests for changed APIs or message formats | Med |
| UI changes: Playwright tests use role/label locators and web-first assertions, not fixed waits | Low |

## 7. Observability
| Check | Typical sev |
|---|---|
| Structured logs with correlation/trace ID and business keys (AWB, flight, booking) | Low |
| No PII/secrets/tokens logged | High |
| Errors logged once at the boundary, not at every layer | Low |
| New critical paths emit metrics/traces (OpenTelemetry) | Low |
| Log level appropriate (no Info spam in hot loops) | Low |
