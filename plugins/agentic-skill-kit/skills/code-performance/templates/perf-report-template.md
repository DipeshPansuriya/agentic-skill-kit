# Performance Report: {component / endpoint}

_Stack: {e.g. .NET 8, EF Core 8} · Environment: {machine / container size, data volume} · Date: {YYYY-MM-DD}_

## 1. Goal
| Metric | Target | Why it matters |
|---|---|---|
| {p95 latency of GET /awb/{id}} | {≤ 300 ms at 200 RPS} | {SLA with handling agent} |

## 2. Baseline (before)
| Metric | Value | How measured |
|---|---|---|
| {p95 latency} | {1,840 ms} | {k6, 200 VUs, 5 min, warm cache} |
| {Allocations / request} | {4.2 MB} | {BenchmarkDotNet MemoryDiagnoser} |

Profiler / trace used: {dotnet-trace cpu-sampling, 60 s under load}. Evidence: {flame graph file / screenshot link}.

## 3. Hotspots
| # | Location (file:line / function) | Share of cost | Root cause | Big-O now | Evidence |
|---|---|---|---|---|---|
| 1 | {ManifestService.cs:88 BuildAsync} | {62 % CPU} | {N+1: shipper query per AWB} | {O(n) queries} | {trace span count = 1 + n} |

## 4. Changes
| # | Change | Big-O after | Behaviour change? | Test proving same behaviour |
|---|---|---|---|---|
| 1 | {Prefetch shippers with one IN query into a dictionary} | {1 query, O(n)} | {None} | {ManifestServiceTests.Build_SameOutput_AsBefore} |

## 5. After
| Metric | Before | After | Delta % |
|---|---|---|---|
| {p95 latency} | {1,840 ms} | {210 ms} | {−88.6 %} |
| {Allocations / request} | {4.2 MB} | {0.6 MB} | {−85.7 %} |

Delta % = (after − before) / before × 100. Same environment, data and load as baseline.

## 6. Risks & trade-offs
| Risk | Mitigation |
|---|---|
| {Dictionary holds all shippers for large manifests} | {Chunk IN list at 1,000 ids} |

## 7. Benchmark / guard added
| Guard | Location | Threshold |
|---|---|---|
| {BenchmarkDotNet ManifestBench} | {bench/ManifestBench.cs} | {Alert if mean > 1.2 × baseline} |
| {Query-count test} | {tests/ManifestQueryCountTests.cs} | {≤ 2 SQL statements per call} |

## 8. Not done / follow-ups
- {SQL plan for shipper lookup: handed to sql-performance-tuning}
