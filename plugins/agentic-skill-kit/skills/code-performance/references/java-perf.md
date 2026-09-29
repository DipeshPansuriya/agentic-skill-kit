# Java Performance (Java 21 · Spring Boot 3)

## Measure first
| Question | Tool | Command / usage |
|---|---|---|
| CPU / allocation / lock profile, prod-safe (~1% overhead) | Java Flight Recorder + JDK Mission Control | `jcmd PID JFR.start duration=120s filename=rec.jfr settings=profile`; open in JMC (Hot Methods, Allocations, Lock Instances) |
| Flame graph incl. native + wall-clock | async-profiler | `asprof -d 60 -e cpu -f cpu.html PID` (`-e alloc`, `-e wall`, `-e lock`) |
| Heap growth / leak | `jcmd PID GC.heap_info`, heap dump + Eclipse MAT | `jcmd PID GC.heap_dump heap.hprof`; MAT "Leak Suspects", dominator tree |
| GC pauses | GC logs | `-Xlog:gc*:file=gc.log:time,uptime,level,tags`; JFR GC events |
| Threads blocked / pool exhausted | `jcmd PID Thread.print`, Actuator `/actuator/metrics` (`hikaricp.connections.pending`, `jvm.threads.*`) | |
| Micro-benchmark | JMH | Never `System.nanoTime` loops: JIT warm-up and dead-code elimination lie |
| Load / latency | Gatling, k6, JMeter + Micrometer/OpenTelemetry | p95/p99 at fixed concurrency |

```java
@State(Scope.Benchmark) @BenchmarkMode(Mode.AverageTime) @OutputTimeUnit(TimeUnit.MICROSECONDS)
@Warmup(iterations = 3) @Measurement(iterations = 5) @Fork(1)
public class UldLookupBench {
    List<String> list; Set<String> set;
    @Setup public void setup() { list = ids(10_000); set = new HashSet<>(list); }
    @Benchmark public boolean listContains() { return list.contains("ULD-9999"); }
    @Benchmark public boolean setContains()  { return set.contains("ULD-9999"); }
}
// Run with -prof gc to see allocation rate
```

## Hotspot → fix
| Hotspot | Fix | Notes |
|---|---|---|
| GC time high / long pauses | Right-size heap (`-Xms` = `-Xmx` in containers or `-XX:MaxRAMPercentage=75`); G1 (default) for most services; ZGC (`-XX:+UseZGC`, generational default from JDK 23; `-XX:+ZGenerational` on 21) for low-pause large heaps; Parallel GC for batch throughput | Reduce allocation first; tune GC second |
| Blocking I/O limits throughput | Virtual threads: `spring.threads.virtual.enabled=true` (Boot 3.2+) | Keep DB pool bounded: virtual threads do not make the DB faster |
| Virtual-thread **pinning** | On JDK 21-23 `synchronized` blocks around blocking I/O pin the carrier: use `ReentrantLock`; detect with JFR `jdk.VirtualThreadPinned` (or `-Djdk.tracePinnedThreads=full` on 21-23) | JDK 24+ (JEP 491) removes most `synchronized` pinning; native/JNI frames still pin |
| ThreadLocal-heavy code on virtual threads | Avoid large per-thread caches; use scoped values when available | Millions of threads × ThreadLocal = memory |
| Streams in very hot tight loops | Plain loop if JMH shows a win; avoid boxing (`mapToInt`, primitive streams) | Streams are fine elsewhere; readability first |
| `parallelStream()` in request code | Remove, or use a dedicated executor | Shares the common ForkJoinPool across the JVM |
| String concat in loop | `StringBuilder` / `String.join` / `Collectors.joining` | Single-expression `+` is already optimized |
| `list.contains` in loop | `HashSet` / `HashMap` | O(n·m) → O(n+m) |
| Regex per call | `private static final Pattern` | `String.matches/split(regex)` compile each call (except 1-char split) |
| Exceptions for flow control | Validate first; `Optional` | Stack trace capture is expensive |
| Logging cost | Parameterized `log.debug("x {}", v)`; guard expensive args with `isDebugEnabled()` | Async appender for high volume |
| Chatty HTTP calls | Batch endpoint, `RestClient`/`WebClient` with connection pooling, timeouts, and caching (`@Cacheable` + Caffeine with `maximumSize`) | Unbounded `ConcurrentHashMap` caches leak |

## JPA / Hibernate
| Smell | Fix |
|---|---|
| N+1 on lazy associations | `JOIN FETCH` in JPQL, `@EntityGraph(attributePaths = "ulds")`, or `hibernate.default_batch_fetch_size=50` |
| `JOIN FETCH` of 2+ collections (MultipleBagFetchException / cartesian) | Fetch one collection per query, or use `Set`, or batch fetching |
| Paging + collection fetch join (in-memory paging warning HHH90003004) | Page IDs first, then fetch by IDs |
| Loading entities to read a few fields | DTO / interface projection, `record` constructor expression |
| `findAll().stream().filter(...)` | Derived query / `@Query` with WHERE |
| `save()` per row in a loop | `saveAll` + `hibernate.jdbc.batch_size=50`, `order_inserts/order_updates=true`; `IDENTITY` ids disable insert batching (use `SEQUENCE`) |
| Long transactions / OSIV hiding lazy loads | `spring.jpa.open-in-view=false`; fetch what the view needs in the service |
| Read-only queries | `@Transactional(readOnly = true)` (skips dirty checking; flush mode manual) |

## Connection pool (HikariCP)
| Setting | Guidance |
|---|---|
| `maximumPoolSize` | Start small: roughly `cores_of_DB × 2 + effective_spindles` (HikariCP wiki); 10-20 is typical. Bigger pools usually increase latency |
| `connectionTimeout` | Fail fast (e.g. 2-5 s) and alert on `hikaricp.connections.pending` |
| Total across instances | `pods × maximumPoolSize` must stay under DB `max_connections` |
| `leakDetectionThreshold` | Enable in test/stage to find unclosed connections |

Slow SQL itself (plans, indexes, locks): hand to sql-performance-tuning.
