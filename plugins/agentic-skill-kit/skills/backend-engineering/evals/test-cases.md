# Test Cases: backend-engineering

Rerun after every edit. Score with the 5-point checklist (correct stack/version, compiles as written, tests included, shared rules applied, usable as-is).

| # | Type | Request | Should trigger? | Expected |
|---|---|---|---|---|
| 1 | Single (.NET) | "Add a minimal API endpoint to cancel a booking by AWB, .NET 8, EF Core" | Yes | `references/dotnet.md` used; `TypedResults`, `CancellationToken`, problem details; xUnit tests for 200/404/409 |
| 2 | Single (.NET) | "Why does this controller deadlock?" + code using `.Result` | Yes | Diagnoses sync-over-async; async fix; explains thread-pool starvation |
| 3 | Single (Java) | "Spring Boot 3 service to list flights by origin with paging" | Yes | `references/java.md`; record DTOs, `Pageable`, `@Transactional(readOnly = true)`; `@WebMvcTest` + `@MockitoBean` test |
| 4 | Single (Java) | "Refactor this to use virtual threads" + Java 21 executor code | Yes | `spring.threads.virtual.enabled` or `Executors.newVirtualThreadPerTaskExecutor()`; pinning caveat; no pooling of virtual threads |
| 5 | Single (Python) | "FastAPI endpoint to upload a manifest CSV and validate rows with Pydantic" | Yes | `references/python.md`; Pydantic v2 APIs; problem details on errors; pytest with `dependency_overrides` |
| 6 | Single (Python) | "Explain what this asyncio code does and why it's slow" + code with `requests` in `async def` | Yes | Explains event-loop blocking; switch to `httpx.AsyncClient` or `def`; no code rewrite beyond need |
| 7 | API design | "Design the REST endpoints and error format for shipment tracking" | Yes | `references/api-design.md`; resource paths, status codes, cursor pagination, RFC 9457 example, OpenAPI notes |
| 8 | Multi-stack | "Angular screen + .NET API to create a booking; give me the API side and the contract" | Yes | .NET code + shared DTO/problem contract; UI handed to frontend-engineering; same field names both sides |
| 9 | Multi-stack | ".NET API publishes an event, Python worker consumes it; write both" | Yes | Both stack files; one message contract; idempotent consumer; correlation ID propagated |
| 10 | Edge: unknown version | "Write a Spring service for bookings" (no build file) | Yes | States assumed Java 21 + Boot 3.x; `jakarta.*` imports; notes what changes for Boot 2/4 |
| 11 | Edge: legacy code | Code using .NET Framework 4.8 `WebClient` and `HttpWebRequest` | Yes | Stays on .NET Framework APIs for the fix; flags `WebClient` obsolete; upgrade path suggested separately |
| 12 | Edge: legacy Python | Code using Pydantic v1 `class Config` / `.dict()` | Yes | Matches v1 for the fix or asks; flags v2 migration (`model_config`, `model_dump`) |
| 13 | Edge: secret in input | User pastes code with a hard-coded DB password | Yes | Moves it to config/secret store; tells user to rotate the leaked secret |
| 14 | Near-miss | "Tune this slow SQL query / add the right index" | **No** (sql-performance-tuning) | |
| 15 | Near-miss | "Review this PR" + diff | **No** (code-review) | |
| 16 | Near-miss | "Should we go microservices or modular monolith for the cargo platform?" | **No** (software-architecture) | |
| 17 | Near-miss | "Build a React table for bookings" | **No** (frontend-engineering) | |
| 18 | Consistency | Run #1 ×3 | Yes | Same output sections (Assumptions → Plan → Code → Tests → Decisions → Needs input) 3/3 |
