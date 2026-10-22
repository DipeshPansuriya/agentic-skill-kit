---
name: backend-engineering
description: Write, refactor, debug and explain backend code with tests for .NET, Java Spring Boot and Python FastAPI or Django. Use when the user asks to build an API or service, fix C#, Java or Python code, add unit tests, or design REST endpoints.
---

# Backend Engineering (.NET · Java · Python)

Produce working, tested backend code that fits the user's stack and existing style, with the trade-offs explained.

## Inputs
- A task in words ("add an endpoint to cancel a booking", "why is this slow?")
- Existing code, stack traces, logs, `.csproj` / `pom.xml` / `build.gradle` / `pyproject.toml`
- API contracts (OpenAPI, sample JSON), DB schema, error messages

If code is given, it wins over the written description when they disagree; flag the conflict.

## Defaults (state them at the top of the answer when used)
| Setting | Default if not stated | Detect from |
|---|---|---|
| .NET | C# 12, .NET 8 LTS, ASP.NET Core minimal APIs, EF Core 8, xUnit | `<TargetFramework>`, `LangVersion`, `Program.cs` style |
| Java | Java 21 LTS, Spring Boot 3.x, Spring Data JPA, JUnit 5 + Mockito | `pom.xml` / `build.gradle` parent + `java.version` |
| Python | Python 3.12, FastAPI + Pydantic v2, pytest, uv + `pyproject.toml` | `requires-python`, lock files, imports |
| API style | REST + JSON, RFC 9457 problem details, OpenAPI 3.1 | Existing controllers / routers |
| Tests | Unit tests for new logic; integration test when I/O is the point | Existing test folder and framework |

Ask **one** question only if the stack or version is unknown *and* the answer changes the code (e.g. Spring Boot 2 vs 3: `javax` vs `jakarta`). Otherwise assume the defaults and say so.

## Which reference to read
| Request is about… | Read |
|---|---|
| C#, ASP.NET Core, EF Core, xUnit, `.csproj` | `references/dotnet.md` |
| Java, Spring Boot, JPA/Hibernate, JUnit, Maven/Gradle | `references/java.md` |
| Python, FastAPI, Django, Pydantic, pytest, uv/pip | `references/python.md` |
| Endpoint shape, status codes, versioning, pagination, errors, idempotency, OpenAPI | `references/api-design.md` (plus the stack file) |
| Several stacks (e.g. .NET API called by a Python worker) | Each stack file; keep one shared contract from `references/api-design.md` |
| None clearly match | Ask one question: which language and framework? |

For full-stack requests (e.g. Angular UI + .NET API), handle the API here and hand the UI part to the frontend-engineering skill; keep the contract (DTOs, error model) identical on both sides.

## Steps
1. **Clarify stack and version.** Detect from the code or build files; otherwise apply Defaults and state them.
2. **Route.** Read the matching reference file(s) from the table above.
3. **Understand the existing code** (if given): naming, layering, DI style, error handling, test framework. Match it.
4. **Plan briefly** (2–5 bullets): files to touch, data flow, failure cases.
5. **Write the code** with a file path heading per file (e.g. `src/Bookings/BookingEndpoints.cs`). Complete, compilable units: imports/usings, types, registrations.
6. **Write tests** for every new branch of logic: happy path, validation failure, not-found/conflict, and one edge case.
7. **Explain key decisions**: why this approach, the trade-off rejected, and anything the user must configure (connection strings, env vars, migrations).
8. **Run the self-check** below and fix before returning.

## Shared rules (all stacks)
- **Validate all input** at the boundary (DTO/record annotations, Pydantic models, FluentValidation or Bean Validation). Never trust client IDs for authorization.
- **No secrets in code** or in committed config. Use env vars, user-secrets, Key Vault, AWS Secrets Manager, or Vault; show placeholders like `${DB_PASSWORD}`.
- **Structured logging** with message templates / key-value fields, never string concatenation. Propagate a **correlation ID** (`traceparent` or `X-Correlation-ID`) and include it in every log line and error response.
- **Never log** passwords, tokens, full card numbers, or personal data.
- **Errors**: return RFC 9457 problem details; never leak stack traces or SQL to clients.
- **Async end to end** for I/O; pass cancellation tokens / timeouts to outbound calls.
- **Parameterised queries only**; no string-built SQL.
- **Tests for new logic** are part of the deliverable, not optional.
- **Match the user's style and versions** when code is shown; do not "upgrade" frameworks silently. Suggest upgrades separately.
- **Don't mix idioms** across stacks (no Java-style getters in C#, no Spring terms in FastAPI answers).
- **Complete snippets**: no `...` or `// TODO` inside critical logic (validation, auth, transactions, error handling).
- **Flag deprecated APIs** you see or must use (e.g. `WebClient` in .NET, `javax.*` in Boot 3, Pydantic v1 `class Config`, `datetime.utcnow()`).
- **Explain trade-offs** in plain words; keep explanations shorter than the code.

## Self-check
- [ ] Stack and version stated (detected or assumed)
- [ ] Correct reference file(s) used; no mixed framework idioms
- [ ] Every file has a path; code compiles as written (imports, types, DI registration)
- [ ] Input validated; errors mapped to problem details; correlation ID logged
- [ ] No secrets, no string-built SQL, no sensitive data in logs
- [ ] Tests cover happy path, validation failure, not-found/conflict, one edge case
- [ ] No `...` or TODO in critical logic
- [ ] Deprecated APIs flagged; existing style and versions respected

## Output
1. **Assumptions** line: stack, version, anything guessed.
2. **Plan** (2–5 bullets).
3. **Code**, one block per file with its path.
4. **Tests**, one block per file with its path, plus the run command (`dotnet test`, `./mvnw test`, `uv run pytest`).
5. **Key decisions & trade-offs** (≤ 6 bullets).
6. **Needs input / next steps**: config, migrations, open questions.

After editing this skill, rerun `evals/test-cases.md`.
