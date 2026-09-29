# Test Cases: code-performance

Rerun after every edit. Score each (0-5): goal metric stated · baseline/after measured or marked Estimate/TBD · hotspot cites file:line · Big-O + behaviour preserved · guard/benchmark added.

| # | Type | Request | Should trigger? | Expected |
|---|---|---|---|---|
| 1 | Single | "This .NET endpoint is slow, p95 is 2 s" + controller looping AWBs with `_context.Shippers.FirstOrDefault` | Yes | Hotspot = N+1 (io-in-loop); one IN query + dictionary; AsNoTracking + projection; query-count test; Delta % template |
| 2 | Single | "Optimize this Python function" (nested loops matching two lists of 50k ULDs) | Yes | Big-O O(n·m) → O(n+m) via dict; timeit/pytest-benchmark before/after; same output order |
| 3 | Single | "Our Spring Boot service has high CPU after enabling virtual threads" | Yes | JFR/async-profiler steps; checks pinning (`synchronized` + I/O on JDK 21-23), Hikari pool size; no guessing numbers |
| 4 | Single | "Memory leak in our .NET worker, pod OOMs every 6 h" | Yes | dotnet-gcdump comparison plan; suspects unbounded static cache/event handlers; bounded IMemoryCache fix |
| 5 | Single | "Speed up this React table with 5,000 rows, typing in the filter lags" | Yes | React Profiler first; virtualization + useDeferredValue; memo only where measured; INP target ≤ 200 ms |
| 6 | Single | "Angular dashboard change detection is slow" | Yes | OnPush + signals, `@for track`, @defer; Angular DevTools profiler baseline |
| 7 | Single | "FastAPI endpoint freezes other requests" + `requests.get` inside `async def` | Yes | blocking-in-async; httpx.AsyncClient shared via lifespan; py-spy evidence |
| 8 | Script | Run `scripts/perf_smells.py templates/samples/` | Yes | Bad samples: HIGH findings in all 4 (exit 1); clean samples: 0 HIGH / 0 MED |
| 9 | Edge: no numbers | "Make this faster" + code only, no metrics | Yes | States no evidence; runs scanner; gives exact measurement commands; improvements labelled **Estimate** |
| 10 | Edge: micro-opt request | "Rewrite with Span and unsafe for speed" on code that runs once per day | Yes | Declines unmeasured micro-optimization; explains readability trade-off; suggests benchmark first |
| 11 | Edge: DB-bound | Trace shows 90 % time in one SQL statement with a scan | Yes (then hand-off) | Captures SQL + timings; hands plan/index work to sql-performance-tuning; fixes only app-side parts |
| 12 | Edge: behaviour | Optimization would change result ordering | Yes | Keeps ordering (or flags as behaviour change needing approval); characterization test |
| 13 | Near-miss | "Why is this SQL query slow? Here is the execution plan" | **No** (sql-performance-tuning) | Plan/index analysis, not app profiling |
| 14 | Near-miss | "Refactor this 400-line method into smaller readable functions" | **No** (refactoring) | Readability refactor, no perf measurement |
| 15 | Near-miss | "Review this PR before merge" | **No** (code-review) | Findings table + verdict |
| 16 | Near-miss | "Design indexes and partitioning for the shipments table" | **No** (database-engineering) | Schema/index design |
| 17 | Consistency | Run #1 three times | Yes | Same top hotspot (N+1), same fix, same report sections 3/3 |
