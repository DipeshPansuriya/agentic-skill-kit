# Python Performance (3.12+)

## Measure first
| Question | Tool | Command / usage |
|---|---|---|
| Which functions cost the most (deterministic) | `cProfile` + `pstats` / snakeviz | `python -m cProfile -o prof.out app.py`; `python -m pstats prof.out` → `sort cumtime`, `stats 20` |
| Live process, no code change, prod-safe (sampling) | `py-spy` | `py-spy top --pid PID`; `py-spy record -o flame.svg --pid PID` (`--idle` to include waiting; `--native` for C-ext) |
| Readable call tree for one request / script | `pyinstrument` | `pyinstrument script.py`; middleware for FastAPI/Django |
| Line-level hotspot inside one function | `line_profiler` | `@profile` + `kernprof -l -v script.py` |
| Micro-timing a snippet | `timeit` | `python -m timeit -s "s=set(range(10**5))" "99999 in s"` |
| Memory growth / leak | `tracemalloc` (stdlib), `memray` | `tracemalloc.start(); snap1=...; snap2.compare_to(snap1, 'lineno')`; `memray run app.py` → `memray flamegraph` |
| Event loop blocked | `asyncio` debug mode | `PYTHONASYNCIODEBUG=1` logs callbacks slower than 100 ms (`loop.slow_callback_duration`) |
| Regression guard | `pytest-benchmark` | `def test_parse(benchmark): benchmark(parse, line)` |

## Hotspot → fix
| Hotspot | Fix | Complexity |
|---|---|---|
| `x in list` inside a loop | Build `set` / `dict` once | O(n·m) → O(n+m) |
| Nested loops joining two lists | Index one side in a dict keyed by the join field | O(n·m) → O(n+m) |
| String `+=` in a loop | `"".join(parts)` or `io.StringIO` | O(n²) worst case → O(n) |
| Row loops over numbers | NumPy vectorized ops / pandas column ops; `np.where`, `merge`, `groupby().agg` | Moves loop to C; 10-100× typical |
| `df.iterrows()` / `apply(axis=1)` | Vectorize; if unavoidable use `itertuples()` | iterrows builds a Series per row |
| Building big lists only to iterate once | Generators / generator expressions | Memory O(n) → O(1) |
| Repeated pure computation | `functools.lru_cache(maxsize=...)` / `cache` on pure functions with hashable args | Unbounded `cache` on high-cardinality args leaks memory; don't cache methods on `self` without care |
| Attribute/global lookups in very tight loops | Bind to a local name | Micro; only if profiled |
| Regex per call | Module-level `re.compile` | `re` caches ~512 patterns, but compile+lookup still costs |
| Many small objects | `__slots__` or `@dataclass(slots=True)` | Cuts memory per instance |
| JSON heavy | `orjson` / `msgspec` | Measure; adds a dependency |
| CPU-bound in threads | GIL: use `ProcessPoolExecutor`, NumPy (releases GIL), or a C-extension/Rust/Cython module | Free-threaded 3.13t build is experimental; C-extensions add build and debugging cost, use last |

## asyncio
| Smell | Fix |
|---|---|
| `time.sleep`, `requests.*`, sync DB driver inside `async def` | `await asyncio.sleep`, `httpx.AsyncClient`, async driver (asyncpg, SQLAlchemy async); or `await asyncio.to_thread(fn)` for unavoidable blocking calls |
| Sequential `await` of independent calls in a loop | `asyncio.gather` / `TaskGroup` bounded with `asyncio.Semaphore(n)` |
| New HTTP client per request | One shared `httpx.AsyncClient` (lifespan), with timeouts and limits |
| CPU-heavy work in the event loop | `loop.run_in_executor(ProcessPoolExecutor(), ...)` |
| FastAPI `def` vs `async def` | Blocking code in `def` endpoints (runs in threadpool); only non-blocking code in `async def` |

## ORM (SQLAlchemy / Django)
| Smell | Fix |
|---|---|
| N+1 on relationships | SQLAlchemy `selectinload` / `joinedload`; Django `select_related` (FK) / `prefetch_related` (M2M, reverse) |
| Loading full rows for a few fields | `load_only`, `with_entities`; Django `.values()` / `.only()` |
| Insert/update per row | `session.execute(insert(T), rows)` (executemany), `bulk_create` / `bulk_update` with `batch_size` |
| `len(qs)` / `if qs:` on big querysets | `.count()` / `.exists()` |
| Django debug toolbar / `connection.queries` | Use in dev to count queries per request |

Slow SQL itself: hand to sql-performance-tuning.
