# .NET Performance (.NET 8+)

## Measure first
| Question | Tool | Command / usage |
|---|---|---|
| Is it CPU, GC, thread pool, or exceptions? (live, prod-safe) | `dotnet-counters` | `dotnet-counters monitor -p PID --counters System.Runtime,Microsoft.AspNetCore.Hosting` |
| Where is CPU time spent? | `dotnet-trace` + PerfView / VS / speedscope | `dotnet-trace collect -p PID --profile cpu-sampling` then `--format speedscope` |
| What allocates? | `dotnet-trace --profile gc-verbose`, VS Allocation tool, dotMemory | Sort by allocated bytes per type / call stack |
| Memory leak? | `dotnet-gcdump` (heap snapshot) / `dotnet-dump` | `dotnet-gcdump collect -p PID`; compare two dumps, look for growing roots (static caches, event handlers) |
| Thread pool starvation? | counters: `threadpool-queue-length`, `threadpool-thread-count` climbing | Usually sync-over-async; confirm with `dotnet-stack report -p PID` |
| Micro-benchmark a method | BenchmarkDotNet | See below; Release build, never Debug |
| End-to-end latency / throughput | k6, NBomber, Bombardier + OpenTelemetry traces | Report p50/p95/p99 and RPS at fixed concurrency |

```csharp
[MemoryDiagnoser]                       // adds Allocated column
public class AwbParseBench
{
    private readonly string _line = "020-12345675 FRA JFK 12 340.5K";
    [Benchmark(Baseline = true)] public Awb Split() => AwbParser.ParseSplit(_line);
    [Benchmark] public Awb Span()  => AwbParser.ParseSpan(_line);
}
// dotnet run -c Release -- --filter *AwbParseBench*
```

## Hotspot → fix
| Hotspot | Fix | Notes |
|---|---|---|
| `.Result`, `.Wait()`, `GetAwaiter().GetResult()` in request path | Async all the way (`await`), pass `CancellationToken` | Causes thread-pool starvation under load, deadlocks with a sync context |
| `async void` (non-event handler) | `async Task` | Exceptions crash the process; cannot await |
| Many small independent awaits in a loop | `Task.WhenAll` with a bound (`Parallel.ForEachAsync(items, new ParallelOptions { MaxDegreeOfParallelism = 8 }, ...)`) | Respect downstream rate limits |
| `new HttpClient()` per call | `IHttpClientFactory` / typed client, or one static `HttpClient` with `SocketsHttpHandler { PooledConnectionLifetime = ... }` | Per-call clients exhaust sockets (TIME_WAIT) |
| High Gen0 allocation rate | Avoid LINQ in tight loops, reuse buffers, `StringBuilder`, `string.Create`, `Span<T>` / `stackalloc` for small parsing | Only where the profiler shows allocation cost; Span can't cross `await` |
| Large temporary arrays (> 85 KB → LOH) | `ArrayPool<T>.Shared.Rent/Return` (return in `finally`), `RecyclableMemoryStream` | Never use a rented array after returning it |
| Boxing / closures in hot loops | Generic methods, static lambdas (`static x => ...`) | Check with allocation profiler |
| Regex constructed per call | `static readonly Regex` or `[GeneratedRegex]` source generator (.NET 7+) | `RegexOptions.Compiled` costs startup; generator is best |
| Exceptions for control flow | `TryParse`, result types | Exceptions cost microseconds each |
| Excess logging | `LoggerMessage` source-generated methods, `IsEnabled` guard; never string interpolation in log calls | Structured templates avoid formatting when level is off |
| Serialization cost | `System.Text.Json` source generation (`JsonSerializerContext`) | Cuts reflection + startup |
| Repeated expensive reads | `IMemoryCache` with size limit + expiration; `HybridCache` (.NET 9) / Redis for multi-node | Unbounded cache = memory leak; set `SizeLimit` |
| Lock contention | Narrow the lock, `ConcurrentDictionary`, `Channel<T>` producer/consumer | Measure with `dotnet-counters` `monitor-lock-contention-count` |

## EF Core
| Smell | Fix |
|---|---|
| Read-only query tracks entities | `.AsNoTracking()` (or `UseQueryTrackingBehavior(NoTracking)` context-wide for read models) |
| Loads whole entities to show 3 fields | Project: `.Select(a => new AwbRow(a.Number, a.Status))` |
| N+1: query per item in a loop / lazy loading | One query: `Where(x => ids.Contains(x.Id))` + dictionary, `Include`, or projection with the child fields |
| Cartesian explosion with several `Include` collections | `.AsSplitQuery()` (measure: more round trips) |
| `ToList()` before `Where` | Keep `IQueryable` until the final materialization |
| `SaveChanges()` inside a loop | Add all, call `SaveChangesAsync` once; bulk: `ExecuteUpdateAsync` / `ExecuteDeleteAsync` (EF 7+) |
| Same query shape executed very often | `EF.CompileAsyncQuery(...)` (measure; EF caches query plans already) |
| Paging with `Skip` on deep pages | Keyset paging (`Where(x => x.Id > lastId).Take(n)`) |
| DbContext creation cost in hot paths | `AddDbContextPool` |

Slow SQL itself (plan, index, statistics, parameter sniffing): hand to sql-performance-tuning with the generated SQL (`ToQueryString()` or logging `Microsoft.EntityFrameworkCore.Database.Command`).
