# OWASP Checklist (Top 10:2025 · API Security Top 10:2023 · CWE)

Use the 2025 IDs in reports. If a team still tracks 2021 IDs, add the mapping in brackets, e.g. "A05:2025 Injection (A03:2021)".

## OWASP Top 10:2025 (web applications)
| 2025 ID | Category | 2021 mapping | Check in code / config | Key CWEs |
|---|---|---|---|---|
| A01 | Broken Access Control | A01 + A10 (SSRF merged here) | Every endpoint has authz; object-level checks (IDOR); deny by default; no trust in client-sent role/tenant IDs; CORS allow-list; SSRF: outbound URLs allow-listed | 22, 200, 284, 285, 639, 862, 863, 918, 942, 352 |
| A02 | Security Misconfiguration | A05 (+ XXE from A05) | Debug off; default creds removed; security headers; verbose errors off; XML parsers with DTD/external entities disabled; cloud storage not public; actuator/swagger not exposed | 16, 489, 611, 614, 1004 |
| A03 | Software Supply Chain Failures | A06 Vulnerable & Outdated Components (expanded) | Lock files committed; SCA in CI; no abandoned packages; pinned CI actions/images; SBOM; signed builds | 1104, 1395, 829 |
| A04 | Cryptographic Failures | A02 | TLS 1.2+ everywhere; no MD5/SHA1 for passwords/signatures; AES-GCM not ECB; keys not in code; CSPRNG for tokens; cert validation on | 259, 295, 321, 326, 327, 328, 330, 338, 798, 916 |
| A05 | Injection | A03 (incl. XSS) | Parameterized SQL/NoSQL; no shell string building; output encoding; no eval; ORM raw-SQL reviewed; LDAP/XPath escaping | 20, 74, 77, 78, 79, 89, 94, 95, 643, 943 |
| A06 | Insecure Design | A04 | Threat model for the flow; rate limits on business flows; server-side validation of business rules (weights, rates, amounts) | 209, 256, 501, 840 |
| A07 | Authentication Failures | A07 Identification & Authentication Failures | MFA for admin; lockout/rate-limit on login; session rotation on login; JWT validated (alg, iss, aud, exp); password hashing Argon2id/bcrypt | 287, 307, 384, 521, 613, 798 |
| A08 | Software or Data Integrity Failures | A08 | No unsafe deserialization; signed updates/webhooks (HMAC); CI/CD integrity | 345, 502, 565, 829 |
| A09 | Security Logging and Alerting Failures | A09 Security Logging & Monitoring Failures | Auth failures and access-control denials logged with correlation ID; no secrets/PII in logs; alerts wired | 117, 223, 532, 778 |
| A10 | Mishandling of Exceptional Conditions | New (parts of old code-quality CWEs) | Fail closed on errors; no stack traces to clients; exceptions don't skip authz/transactions; resource cleanup | 209, 248, 252, 390, 391, 636, 755 |

## OWASP API Security Top 10:2023
| ID | Risk | What to check | Typical fix |
|---|---|---|---|
| API1 | Broken Object Level Authorization (BOLA / IDOR) | `GET /awb/{id}` returns any tenant's AWB | Query scoped by tenant/owner from the token: `WHERE Id = @id AND TenantId = @tenantFromClaims` |
| API2 | Broken Authentication | Missing token validation, weak reset flow, no brute-force limits | Framework JWT validation, rate limit, short-lived tokens |
| API3 | Broken Object Property Level Authorization | Mass assignment; response exposes internal fields | Separate request/response DTOs; allow-list bindable fields |
| API4 | Unrestricted Resource Consumption | No pagination/size limits/timeouts/rate limits | Max page size, body size limit, rate limiting, timeouts |
| API5 | Broken Function Level Authorization | Non-admin can call `/admin/*` or `DELETE` | Role/policy per endpoint; deny by default |
| API6 | Unrestricted Access to Sensitive Business Flows | Bulk booking / quote scraping automation | Rate limits per account, CAPTCHA/device checks, business caps |
| API7 | Server Side Request Forgery | Fetches user-supplied URL (webhook, document import) | Allow-list hosts/schemes, block private/link-local IPs after DNS resolution, no redirects |
| API8 | Security Misconfiguration | CORS `*` + credentials, verbose errors, missing headers | Hardened defaults per `references/secrets-and-config.md` |
| API9 | Improper Inventory Management | Old `/v1` still live without auth; undocumented endpoints | API inventory/OpenAPI, retire old versions, gateway |
| API10 | Unsafe Consumption of APIs | Trusting partner/airline API responses blindly | Validate schema, TLS on, timeouts, size limits |

## Manual checklist per change (tick what was checked; report it)
| Area | Check |
|---|---|
| Input | All external input validated (type, length, range, format e.g. AWB `^\d{3}-\d{8}$`) at the boundary |
| Injection | SQL/NoSQL parameterized; no string-built commands, LDAP, XPath, templates |
| Output | Framework auto-escaping kept; no raw HTML sinks without sanitizer |
| AuthN | Endpoints require auth unless explicitly public; JWT validation parameters set |
| AuthZ | Object-level (tenant/owner) and function-level checks server-side |
| Secrets | None in code, config, tests, Dockerfiles, CI YAML, notebooks |
| Crypto | Approved algorithms; CSPRNG; TLS validation on |
| Files | Upload type/size checks; paths canonicalized and confined (path traversal CWE-22) |
| Outbound | SSRF controls; timeouts; TLS |
| Deserialization | Only safe formats with fixed types |
| Errors / logging | Problem details without internals; no PII/secrets in logs |
| Dependencies | SCA run; Critical/High with fixes upgraded |
| Headers / CORS / CSRF | See `references/secrets-and-config.md` |
