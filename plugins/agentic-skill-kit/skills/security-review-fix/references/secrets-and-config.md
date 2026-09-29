# Secrets, Configuration, Headers, CORS, Logging, Containers

## Exposed secret: response playbook
| Step | Action | Why |
|---|---|---|
| 1 | **Rotate / revoke** the secret at its issuer (IAM key, DB password, API key, signing key) | Removing it from code does not remove it from git history, forks, CI logs, caches |
| 2 | Check the issuer's access logs for use since the commit date | Detect abuse |
| 3 | Move the value to a secret store and reference it by name | Prevent recurrence |
| 4 | Purge history only if policy requires (`git filter-repo`, BFG) and force-push with team coordination | Optional; rotation is mandatory |
| 5 | Add pre-commit + CI secret scanning (gitleaks, GitHub push protection) | Guard |

Never print a secret in a report: show the first 4 characters + `****`.

## Where secrets belong
| Stack / platform | Local dev | Deployed |
|---|---|---|
| .NET | `dotnet user-secrets` | Azure Key Vault (`AddAzureKeyVault`) / AWS Secrets Manager; managed identity for SQL (`Authentication=Active Directory Managed Identity`) |
| Spring Boot | `.env` not committed, `application-local.yml` in `.gitignore` | Spring Cloud Vault / AWS Secrets Manager / Azure Key Vault starters; `${DB_PASSWORD}` placeholders |
| Python | `.env` + `python-dotenv` (gitignored) | Env vars injected from secret store; `pydantic-settings` with `SecretStr` |
| Frontend | No secrets at all: bundles are public | Backend/BFF holds keys |
| Kubernetes | – | External Secrets Operator / CSI Secrets Store; plain `Secret` is only base64, enable etcd encryption |
| CI/CD | – | Pipeline secret variables / OIDC federation to cloud (no long-lived keys) |

## Config hardening
| Item | Secure setting |
|---|---|
| Debug / dev pages | `ASPNETCORE_ENVIRONMENT=Production`, `UseDeveloperExceptionPage` only in Development; Django `DEBUG=False`; Flask debug off |
| Error responses | RFC 9457 problem details, no stack traces / SQL |
| Spring Actuator | `management.endpoints.web.exposure.include=health,info` |
| Swagger / OpenAPI UI | Disabled or authenticated in production |
| Cookies | `Secure`, `HttpOnly`, `SameSite=Lax` (or `Strict`); `__Host-` prefix for session cookies |
| TLS | TLS 1.2+ (prefer 1.3), HSTS on HTTPS sites |
| XML | DTD processing disabled (Cargo-XML, SOAP) |

## Security headers (web responses)
| Header | Recommended value | Notes |
|---|---|---|
| `Content-Security-Policy` | `default-src 'self'; script-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'` | Nonces/hashes instead of `'unsafe-inline'`; roll out with `Report-Only` first |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | Only over HTTPS |
| `X-Content-Type-Options` | `nosniff` | |
| `Referrer-Policy` | `strict-origin-when-cross-origin` or `no-referrer` | |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=()` | Adjust to features used |
| `X-Frame-Options` | `DENY` | Superseded by CSP `frame-ancestors`, keep for old browsers |
| `X-XSS-Protection` | Do not set (or `0`) | Deprecated |
| `Server` / `X-Powered-By` | Remove | Information disclosure |

## CORS
| Pattern | Risk | Fix |
|---|---|---|
| Any origin (`*`) without credentials | Low for truly public data | Keep only for public, cookie-less endpoints |
| Reflecting request `Origin` + `Access-Control-Allow-Credentials: true` | High: any site can read authenticated responses | Exact allow-list: `WithOrigins("https://portal.example.com")` / `allowedOrigins(List.of(...))` / `allow_origins=[...]` |
| `null` origin allowed | High (sandboxed iframes send `null`) | Never allow `null` |
| Regex allow-list `.*example.com` | Matches `evil-example.com` | Anchor: `^https://([a-z0-9-]+\.)?example\.com$` |

Note: browsers reject literal `*` combined with credentials, which is why frameworks "fix" it by reflecting the origin: that reflection is the real vulnerability.

## Logging sensitive data (CWE-532)
| Never log | Log instead |
|---|---|
| Passwords, tokens, API keys, session IDs, Authorization headers | Token type + last 4 chars of a hash, or nothing |
| Passport / ID numbers, DOB, full names with travel data (PNR/APIS), emails, phone | Internal IDs (customer ID, AWB number where not personal), masked values (`P****123`) |
| Payment card data (PAN, CVV) | Nothing (PCI DSS); tokenized reference |
| Full request/response bodies of customs/APIS messages | Message ID, type, status, size |

Also: prevent log injection (CWE-117) by using structured logging templates, not concatenated user input.

## Container basics
| Check | Secure pattern |
|---|---|
| Base image | Minimal, pinned by digest (`mcr.microsoft.com/dotnet/aspnet:8.0@sha256:...`, distroless, `-slim`/`-alpine`) |
| User | `USER app` / non-root UID; `readOnlyRootFilesystem: true` in k8s |
| Secrets | Never `ENV DB_PASSWORD=...` or `COPY .env`; use runtime injection or BuildKit `--mount=type=secret` |
| Build | Multi-stage; no SDK/compilers in the runtime image |
| Scan | `trivy image app:tag`, `trivy config .` for Dockerfile/k8s/Terraform |
| Capabilities | `securityContext: { allowPrivilegeEscalation: false, capabilities: { drop: ["ALL"] } }` |
