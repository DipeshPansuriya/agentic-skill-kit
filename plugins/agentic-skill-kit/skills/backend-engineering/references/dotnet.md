# .NET Reference (C# 12 / .NET 8 LTS, ASP.NET Core)

Default target: `net8.0` (LTS). If the project targets `net9.0` (STS) or `net10.0` (LTS, Nov 2025), use its features but say so. If it targets .NET Framework 4.x, stay on Framework APIs and flag the upgrade path separately.

## Project structure
```
src/Cargo.Api/                 Program.cs, endpoints/controllers, DI wiring
src/Cargo.Application/         use cases, DTOs, validators, interfaces
src/Cargo.Domain/              entities, value objects, domain rules (no framework refs)
src/Cargo.Infrastructure/      EF Core DbContext, migrations, HTTP clients
tests/Cargo.Api.Tests/         xUnit, WebApplicationFactory integration tests
tests/Cargo.Application.Tests/ xUnit unit tests
Directory.Build.props          <Nullable>enable</Nullable>, <TreatWarningsAsErrors>, LangVersion
```
Small services: one project with feature folders (`Bookings/`, `Flights/`) is fine. Match what exists.

## Idioms & conventions
| Topic | Do | Avoid |
|---|---|---|
| APIs | Minimal APIs with `MapGroup` + `TypedResults`, or `[ApiController]` controllers if the repo uses them | Mixing both styles in one feature |
| DTOs | `record` / `sealed record`; `required` members | Exposing EF entities directly |
| DI | Constructor or primary-constructor injection; `AddScoped` for DbContext-dependent services | Service locator (`IServiceProvider.GetService` in business code) |
| Async | `async Task`, `await` all the way, pass `CancellationToken` | `.Result`, `.Wait()`, `async void` (except event handlers) |
| Nullability | `<Nullable>enable</Nullable>`; handle `null` explicitly | `!` null-forgiving to silence warnings |
| Config | `IOptions<T>` / `IOptionsMonitor<T>` + `ValidateDataAnnotations().ValidateOnStart()` | Reading `IConfiguration["x"]` deep in services |
| HTTP clients | `IHttpClientFactory` / typed clients; resilience via `Microsoft.Extensions.Http.Resilience` | `new HttpClient()` per call; `WebClient` / `HttpWebRequest` (obsolete, SYSLIB0014) |
| EF Core | `AsNoTracking()` for reads, projections with `Select`, migrations | Lazy loading by default; `FromSqlRaw` with concatenated strings |
| Time | `TimeProvider` (.NET 8) for testable time | `DateTime.Now` in logic |

## Error handling
- `builder.Services.AddProblemDetails()` + `app.UseExceptionHandler()` → RFC 9457 responses.
- Implement `IExceptionHandler` (.NET 8) to map domain exceptions (e.g. `NotFoundException` → 404, `ConflictException` → 409).
- Validation: return `TypedResults.ValidationProblem(errors)`; FluentValidation is common in existing repos. (.NET 10 adds built-in minimal-API validation via `AddValidation()`.)
- Don't use exceptions for expected flow (not found, invalid input) in hot paths; return results.

## Logging
- `ILogger<T>` with message templates: `logger.LogInformation("Booking {BookingId} created for {Awb}", id, awb);`
- High-volume paths: `[LoggerMessage]` source-generated methods.
- Correlation: `Activity.Current?.TraceId` (W3C `traceparent`) is set automatically; add scopes with `logger.BeginScope`. Export with OpenTelemetry or Serilog if the repo uses it.

## Config & secrets
- `appsettings.json` → `appsettings.{Environment}.json` → env vars (`ConnectionStrings__Cargo`) → user-secrets (dev) → Azure Key Vault / AWS Secrets Manager (prod).
- Never commit connection strings with passwords. Use `dotnet user-secrets set "ConnectionStrings:Cargo" "..."` locally.

## Testing
- xUnit + `Assert` (or FluentAssertions/Shouldly if already used; note FluentAssertions v8 has a commercial licence).
- Mocks: NSubstitute or Moq (match the repo).
- API tests: `WebApplicationFactory<Program>`; real DB via Testcontainers (`Testcontainers.MsSql` / `Testcontainers.PostgreSql`). Avoid EF InMemory provider for query behaviour.
- Run: `dotnet test`.

## Performance pitfalls
- N+1 queries: use `Include` or projection; check with `LogTo`/`EnableSensitiveDataLogging` only in dev.
- Sync-over-async and thread-pool starvation (`.Result`).
- Loading whole tables: always page (`Skip/Take` or keyset).
- Large JSON: stream with `IAsyncEnumerable<T>`.
- Tracking queries for read-only paths; forgetting `AsSplitQuery` on big multi-`Include`s.

## Security pitfalls
- Missing `[Authorize]` / `.RequireAuthorization()`; use policies, check resource ownership.
- Over-posting: bind to DTOs, not entities.
- `FromSqlRaw($"...{input}")` → use `FromSql($"...{input}")` (parameterised interpolation) or parameters.
- `BinaryFormatter` is removed/obsolete; never deserialize untrusted types polymorphically.
- CORS `AllowAnyOrigin()` with credentials; missing HTTPS/HSTS in prod.

## Snippet: minimal API with validation, EF Core, problem details
```csharp
// src/Cargo.Api/Bookings/BookingEndpoints.cs
using System.Text.RegularExpressions;
using Microsoft.AspNetCore.Http.HttpResults;
using Microsoft.EntityFrameworkCore;

namespace Cargo.Api.Bookings;

public sealed record CreateBookingRequest(string AwbNumber, int Pieces, decimal WeightKg);
public sealed record BookingResponse(Guid Id, string AwbNumber, int Pieces, decimal WeightKg);

public static class BookingEndpoints
{
    public static RouteGroupBuilder MapBookings(this IEndpointRouteBuilder app)
    {
        var group = app.MapGroup("/api/v1/bookings").WithTags("Bookings");
        // Production: chain .RequireAuthorization() once AddAuthentication(...) is configured.
        group.MapGet("/{id:guid}", GetById).WithName("GetBooking");
        group.MapPost("/", Create);
        return group;
    }

    private static async Task<Results<Ok<BookingResponse>, NotFound>> GetById(
        Guid id, CargoDbContext db, CancellationToken ct)
    {
        var booking = await db.Bookings.AsNoTracking()
            .Where(b => b.Id == id)
            .Select(b => new BookingResponse(b.Id, b.AwbNumber, b.Pieces, b.WeightKg))
            .FirstOrDefaultAsync(ct);

        return booking is null ? TypedResults.NotFound() : TypedResults.Ok(booking);
    }

    private static async Task<Results<CreatedAtRoute<BookingResponse>, ValidationProblem>> Create(
        CreateBookingRequest request, CargoDbContext db, ILoggerFactory loggerFactory, CancellationToken ct)
    {
        var errors = new Dictionary<string, string[]>();
        if (!Regex.IsMatch(request.AwbNumber ?? "", @"^\d{3}-\d{8}$"))
            errors[nameof(request.AwbNumber)] = ["AWB must look like 176-12345675."];
        if (request.Pieces is < 1 or > 9999)
            errors[nameof(request.Pieces)] = ["Pieces must be between 1 and 9999."];
        if (request.WeightKg <= 0)
            errors[nameof(request.WeightKg)] = ["Weight must be greater than 0."];
        if (errors.Count > 0)
            return TypedResults.ValidationProblem(errors);

        var booking = new Booking { AwbNumber = request.AwbNumber!, Pieces = request.Pieces, WeightKg = request.WeightKg };
        db.Bookings.Add(booking);
        await db.SaveChangesAsync(ct);

        loggerFactory.CreateLogger("Bookings")
            .LogInformation("Booking {BookingId} created for AWB {Awb}", booking.Id, booking.AwbNumber);

        var response = new BookingResponse(booking.Id, booking.AwbNumber, booking.Pieces, booking.WeightKg);
        return TypedResults.CreatedAtRoute(response, "GetBooking", new { id = booking.Id });
    }
}

public sealed class Booking
{
    public Guid Id { get; init; } = Guid.NewGuid();
    public required string AwbNumber { get; init; }
    public int Pieces { get; set; }
    public decimal WeightKg { get; set; }
}

public sealed class CargoDbContext(DbContextOptions<CargoDbContext> options) : DbContext(options)
{
    public DbSet<Booking> Bookings => Set<Booking>();
}
```
```csharp
// src/Cargo.Api/Program.cs
using Cargo.Api.Bookings;
using Microsoft.EntityFrameworkCore;

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddProblemDetails();
builder.Services.AddDbContext<CargoDbContext>(o =>
    o.UseSqlServer(builder.Configuration.GetConnectionString("Cargo")));

var app = builder.Build();
app.UseExceptionHandler();
app.UseStatusCodePages();
app.MapBookings();
app.Run();

public partial class Program { } // exposes Program to WebApplicationFactory
```
```csharp
// tests/Cargo.Api.Tests/BookingValidationTests.cs  (xUnit + Microsoft.AspNetCore.Mvc.Testing)
using System.Net;
using System.Net.Http.Json;
using Microsoft.AspNetCore.Mvc.Testing;

public class BookingValidationTests(WebApplicationFactory<Program> factory)
    : IClassFixture<WebApplicationFactory<Program>>
{
    [Fact]
    public async Task Create_with_bad_awb_returns_400_problem_details()
    {
        var client = factory.CreateClient();
        var response = await client.PostAsJsonAsync("/api/v1/bookings",
            new { awbNumber = "bad", pieces = 1, weightKg = 10m });

        Assert.Equal(HttpStatusCode.BadRequest, response.StatusCode);
        Assert.Equal("application/problem+json", response.Content.Headers.ContentType?.MediaType);
    }
}
```
