# Test Cases: refactoring

Rerun after every edit. Score each (0-5): mode + defaults stated · safety net before changes · behaviour preserved (no mixed-in fixes) · metrics from the script (before/after) · report format and hand-offs.

| # | Type | Request | Should trigger? | Expected |
|---|---|---|---|---|
| 1 | Single (.NET) | "Refactor this 200-line C# `InvoiceService.Calculate` method, it's unreadable" | Yes | Mode `restructure`; xUnit characterization tests first; Extract Method / guard clauses / constants; signature kept; `--compare` metrics |
| 2 | Single (Java) | "Clean up this Spring Boot BookingService, lots of copy-paste" | Yes | Mode `tidy`/`restructure`; duplicate blocks from metrics removed via Extract Method; JUnit tests; no Lombok added if repo doesn't use it |
| 3 | Single (Python) | "Simplify this Python function with nested ifs for rate breaks" | Yes | Guard clauses + lookup table; `== True` / boundary quirks preserved; golden-master check like `check_python_equivalence.py` |
| 4 | Single (React) | "Make this React component maintainable, it has useEffect copying props into state" | Yes | Derived value computed in render; notes first-render difference as behaviour to confirm; tests with Testing Library |
| 5 | Single (Angular) | "Refactor this Angular component with nested subscribes" | Yes | `switchMap`/`mergeMap` choice explained (cancellation semantics); unsubscribe handled; template `awb()` change noted |
| 6 | SQL proc (T-SQL) | "This stored procedure with a cursor is a mess, clean it up" | Yes | Set-based rewrite, CTE, guard + RETURN; NULL/empty-set semantics preserved; `EXCEPT` both ways + counts check; perf claims left to sql-performance-tuning |
| 7 | SQL (PL/pgSQL) | "Refactor this PL/pgSQL function that loops with RETURN NEXT" | Yes | `RETURN QUERY` + CTE + `CASE`; signature unchanged; `EXCEPT ALL` both ways check |
| 8 | Minimize + Ponytail present | "Shorten this module as much as possible, use ponytail" (ponytail commands listed) | Yes | Mode `minimize`; tests first; intensity `full` (or `ultra` only with good coverage); `/ponytail-review` on diff; suggestions filtered by tests + readability; metrics compare |
| 9 | Ponytail missing | "Reduce this code with ponytail" (no ponytail skill/commands available) | Yes | Says it is not installed; gives install commands for the user's agent; **asks before installing**; continues with the minimize ladder |
| 10 | No tests | "Refactor this legacy VB-style C# class, there are no tests" | Yes | Mode `legacy`; characterization tests written first (edge cases, exception messages); seams for DB/clock; no behaviour change |
| 11 | Waiver | "No time for tests, just tidy this file" | Yes | Only `tidy` steps; report says "Safety net: waived by user" with risk |
| 12 | Huge file | "This 3,000-line Python file is unmaintainable, fix it" | Yes | Metrics run first; hotspots ranked; split plan; moves before edits; delivered in checkpoints with follow-ups |
| 13 | Mixed ask | "Refactor this and also fix the SQL injection in it" | Yes (refactor part) | Refactor done; injection listed separately and handed to security-review-fix (or done as a separate labelled step) |
| 14 | Near-miss | "Review my PR before merge and give a verdict" | **No** (code-review) | Findings table + verdict, no refactor |
| 15 | Near-miss | "Speed up this C# method, it takes 3 seconds" | **No** (code-performance) | Profiling / perf fix, not a refactor |
| 16 | Near-miss | "Fix the SQL injection in this login query" | **No** (security-review-fix) | Parameterized fix, not a refactor |
| 17 | Near-miss | "This query takes 40 seconds, tune it" | **No** (sql-performance-tuning) | Plan/index analysis |
| 18 | Near-miss | "Add a cancel-booking endpoint to the .NET API" | **No** (backend-engineering) | New feature code |
| 19 | Consistency | Run #3 three times | Yes | Same mode, same named steps, same metrics numbers (script output), equivalence check passes 3/3 |
