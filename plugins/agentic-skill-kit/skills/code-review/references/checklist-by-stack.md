# Stack-Specific Checks

Apply the section(s) matching the files in the change, on top of `checklist-general.md`.

## .NET (C#, ASP.NET Core, EF Core)
| # | Check | Sev |
|---|---|---|
| 1 | No `.Result` / `.Wait()` / `async void` (except event handlers); `CancellationToken` passed through | Med |
| 2 | `HttpClient` from `IHttpClientFactory` (or long-lived); resilience via `Microsoft.Extensions.Http.Resilience` / Polly with timeouts | Med |
| 3 | EF Core: `AsNoTracking()` for reads; no lazy-loading N+1; `FromSqlRaw` with interpolation replaced by `FromSql`/parameters | High |
| 4 | `[Authorize]` / policy on new controllers/endpoints; no `[AllowAnonymous]` by accident | High |
| 5 | `IDisposable`/`IAsyncDisposable` in `using`; DbContext scoped, never singleton | Med |
| 6 | Nullable reference types respected; no `!` suppression hiding real nulls | Med |
| 7 | `decimal` for money/weight; `DateTimeOffset`/UTC for timestamps | High |
| 8 | Options/secrets from configuration + Key Vault, not hard-coded; `ILogger` with message templates, not string interpolation | Low |

## Java / Spring Boot
| # | Check | Sev |
|---|---|---|
| 1 | `@Transactional` on public methods called from outside the bean (self-invocation bypasses the proxy) | High |
| 2 | JPA: no N+1 (use fetch joins / entity graphs); `open-in-view` disabled | Med |
| 3 | Queries use bind parameters / Criteria; no string-concatenated JPQL/native SQL | High |
| 4 | Spring Security: new endpoints covered by `SecurityFilterChain` / method security (`@PreAuthorize`) | High |
| 5 | `RestClient`/`WebClient` with connect + read timeouts; Resilience4j for retries/circuit breaker | Med |
| 6 | Kafka/JMS listeners idempotent; manual ack after successful processing; DLT configured | High |
| 7 | `BigDecimal` with explicit scale/rounding; `Instant`/`OffsetDateTime` not `Date` | High |
| 8 | Virtual threads (Java 21+): no long `synchronized` blocks around I/O (pinning) | Med |

## Python
| # | Check | Sev |
|---|---|---|
| 1 | No mutable default args (`def f(x=[])`) | Med |
| 2 | SQL via parameters (`cursor.execute(sql, params)` / SQLAlchemy bound params); no f-string SQL | High |
| 3 | No `pickle`/`yaml.load` (use `yaml.safe_load`) / `eval` on untrusted data | High |
| 4 | `requests`/`httpx` calls have `timeout=`; sessions reused | Med |
| 5 | No bare `except:` / `except Exception: pass` | Med |
| 6 | Async code does not call blocking I/O (use `asyncio.to_thread` or async clients) | Med |
| 7 | `Decimal` for money; timezone-aware `datetime` (`datetime.now(UTC)`) | High |
| 8 | Type hints on public functions; Pydantic/validation at API boundaries | Low |

## React (TypeScript)
| # | Check | Sev |
|---|---|---|
| 1 | No `dangerouslySetInnerHTML` with unsanitized data (use DOMPurify if unavoidable) | High |
| 2 | `useEffect` deps complete; cleanup for subscriptions/timers/aborts (`AbortController`) | Med |
| 3 | Stable, unique `key` on lists (not array index for reorderable lists) | Med |
| 4 | Server state via a query library (TanStack Query / RTK Query), not hand-rolled fetch-in-effect with races | Low |
| 5 | No tokens in `localStorage` when httpOnly cookies are possible; no secrets in client bundle | High |
| 6 | Large lists (shipment grids) virtualized; expensive renders memoized only where measured | Low |
| 7 | Accessibility: labels on inputs, buttons not `div`s, keyboard reachable | Low |

## Angular
| # | Check | Sev |
|---|---|---|
| 1 | Subscriptions cleaned up (`takeUntilDestroyed`, `async` pipe, or signals) | Med |
| 2 | No `bypassSecurityTrust*` on user data | High |
| 3 | `OnPush` change detection / signals for heavy components; no function calls in templates on hot paths | Low |
| 4 | `@for` with `track` (or `trackBy`) on large lists | Low |
| 5 | HTTP errors handled (interceptor or `catchError`); no nested `subscribe` (use `switchMap`/`concatMap`) | Med |
| 6 | Route guards for protected routes; authz still enforced server-side | High |
| 7 | Typed reactive forms with validators matching server rules | Low |

## SQL (SQL Server / PostgreSQL)
| # | Check | Sev |
|---|---|---|
| 1 | Dynamic SQL uses `sp_executesql` with parameters / `format('%I', …)` + bind params in PG | High |
| 2 | WHERE/JOIN columns indexed; no functions on indexed columns (non-sargable) | Med |
| 3 | No `SELECT *` in application queries or views used by apps | Low |
| 4 | Migrations are backward compatible (expand → migrate → contract); large table changes online / batched | High |
| 5 | Transactions short; correct isolation (SQL Server: consider RCSI; avoid `NOLOCK` for correctness-critical reads) | Med |
| 6 | `UPDATE`/`DELETE` have a WHERE and are batched for large volumes | High |
| 7 | Correct types: `decimal(p,s)` for money/weight, `datetimeoffset`/`timestamptz` for events | Med |
| 8 | Upserts race-safe (`INSERT … ON CONFLICT` in PG; `MERGE` with `HOLDLOCK` or unique constraint + retry in SQL Server) | Med |
