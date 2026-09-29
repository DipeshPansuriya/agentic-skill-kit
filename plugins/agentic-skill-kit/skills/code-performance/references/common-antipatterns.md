# Common Performance Anti-patterns (all stacks)

Each row: what `scripts/perf_smells.py` rule (if any) finds it, the typical cost, and the fix. Confirm with a profiler before changing code.

| # | Anti-pattern | Before (smell) | After (fix) | Big-O / cost | Scanner rule |
|---|---|---|---|---|---|
| 1 | DB call in a loop (N+1) | `foreach (id in ids) db.Awbs.Find(id)` | One query: `db.Awbs.Where(a => ids.Contains(a.Id)).ToDictionary(a => a.Id)` | N round trips → 1 (latency × N) | `io-in-loop` |
| 2 | HTTP call in a loop | `for u in awbs: requests.get(f"/status/{u}")` | Batch endpoint; or bounded concurrency (`gather` + `Semaphore`) | N × RTT → ~N/k × RTT or 1 | `io-in-loop` |
| 3 | ORM lazy-load N+1 | `for o in orders: o.items` (lazy) | `selectinload` / `JOIN FETCH` / `Include` / `prefetch_related` | 1+N queries → 1-2 | Not detectable by regex: count queries in logs |
| 4 | Save per row | `repo.save(x)` / `SaveChanges()` in loop | `saveAll` + JDBC batching / one `SaveChangesAsync` / bulk insert | N commits → 1 | `io-in-loop` |
| 5 | String concat in loop | `s += line` | `StringBuilder` / `"".join()` / `array.join('')` | O(n²) → O(n) | `string-concat-loop` |
| 6 | Linear lookup in loop | `if (list.contains(x))` inside loop | `HashSet` / `set` / `Map` built once | O(n·m) → O(n+m) | `linear-lookup-loop` |
| 7 | Nested loop join | `for a in A: for b in B: if a.id == b.id` | `by_id = {b.id: b for b in B}` | O(n·m) → O(n+m) | Partly (`linear-lookup-loop`) |
| 8 | Sync-over-async | `.Result`, `.Wait()`, `GetAwaiter().GetResult()` | `await` end to end | Thread-pool starvation → latency cliffs | `sync-over-async` |
| 9 | Blocking call in async code | `time.sleep` / `requests` in `async def` | `asyncio.sleep` / `httpx.AsyncClient` / `to_thread` | Stalls every request on the loop | `blocking-in-async` |
| 10 | Sequential independent awaits | `for x in xs: await call(x)` | Bounded `Task.WhenAll` / `Promise.all` / `gather` | Σ latency → max latency | `await-in-loop` |
| 11 | Regex compiled repeatedly | `new Regex(p)` / `Pattern.compile(p)` per call | Static readonly / `[GeneratedRegex]` / module constant | Compile cost per call → once | `regex-in-loop`, `regex-per-call` |
| 12 | Unbounded cache | `static Dictionary` / `@cache` on high-cardinality keys | Size-limited LRU with TTL (`IMemoryCache` SizeLimit, Caffeine `maximumSize`, `lru_cache(maxsize)`) | Memory leak → OOM | Manual |
| 13 | Chatty API | UI calls `/awb/{id}` 50× per screen | Batch/aggregate endpoint, BFF, GraphQL/field selection | 50 RTT → 1 | Manual (network tab) |
| 14 | Missing pagination | `GET /shipments` returns all rows | Keyset / cursor pagination with max page size | Unbounded payload → fixed | Manual; `select-star` hints over-fetch |
| 15 | Over-fetching columns | `SELECT *` / full entities | Projection / DTO | Less I/O, enables covering index | `select-star`, `filter-in-memory` |
| 16 | Filter in memory | `ToList().Where(...)`, `findAll().stream().filter` | Filter in the query | Loads whole table → rows needed | `filter-in-memory` |
| 17 | Excessive logging in hot path | `log.info` / `console.log` / `print` per item | Summary log, level guard, sampling | I/O + allocation per item | `log-in-loop` |
| 18 | Sleep as retry/wait | `Thread.sleep(5000)` in request code | Retry policy with backoff + jitter (Polly, Resilience4j, tenacity), scheduler | Blocks worker threads | `sleep-in-code` |
| 19 | New client per call | `new HttpClient()` / `requests.get` without session | `IHttpClientFactory` / shared `requests.Session` / `httpx.Client` | TCP+TLS handshake per call, socket exhaustion | Manual |
| 20 | Exceptions as control flow | `try { int.Parse } catch` in loops | `TryParse` / validation | µs per throw | Manual |
| 21 | Row-by-row dataframe | `df.iterrows()` | Vectorized column ops | Python loop → C loop | `pandas-iterrows` |
| 22 | Serial work that could stream | Build full list then process | Generator / `IAsyncEnumerable` / Java `Stream` | Memory O(n) → O(1) | Manual |

## Judgement rules
| Situation | Decision |
|---|---|
| Fix saves < 5 % of the measured goal metric and hurts readability | Don't do it; note it |
| Algorithmic win (Big-O) available | Do it before any micro-optimization |
| Hotspot is a SQL statement (plan, index, locks) | Hand to sql-performance-tuning with the captured SQL and timings |
| Hotspot is code structure/readability only, not speed | Hand to refactoring |
