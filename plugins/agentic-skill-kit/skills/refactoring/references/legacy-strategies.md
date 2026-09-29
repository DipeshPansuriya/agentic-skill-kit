# Legacy Strategies

Legacy code = code without tests that people are afraid to change. The order is always:
**pin behaviour → create a seam → change in small steps → remove the old path.**

## 1. Characterization tests (golden master)
Tests that record what the code *does today*, not what it should do. Bugs get pinned too;
fixing them is a separate, labelled change.

1. Pick the entry point (public method, endpoint, proc).
2. Build inputs: typical cases, every branch you can see, boundaries (0, negative, null, empty,
   max, exactly-on-threshold), invalid input (capture the exception type and message).
3. Run the current code, store the outputs as the expected values (a snapshot file is fine).
4. Assert the new code gives the same outputs. Also compare side effects: DB rows, files, messages sent.

| Stack | Tool / pattern |
|---|---|
| .NET | xUnit `[Theory]` + `[MemberData]`; snapshot with Verify (`Verify.Xunit`) if already used |
| Java | JUnit 5 `@ParameterizedTest` + `@CsvFileSource`; ApprovalTests if already used |
| Python | `pytest.mark.parametrize`; snapshot via a JSON file; see `templates/samples/check_python_equivalence.py` (old vs new on 33k inputs) |
| React / Angular | Jest / Vitest render + `toMatchSnapshot()` / Testing Library queries on visible text |
| SQL | Result-equivalence query in `sql-refactoring.md` |

Non-determinism (time, random, GUIDs, ordering): inject a clock / seed, or normalise before
comparing (sort rows, mask ids). A test that is flaky before the refactor proves nothing after.

**Waiver:** if the user says "no tests, just refactor", proceed only with `tidy`-level changes
(rename, extract, constants, formatting), mark the report **Safety net: waived by user** and
list the risk under Risks.

## 2. Seams (places to change behaviour without editing the code there)
| Seam | How | Use for |
|---|---|---|
| Object seam | Extract interface, inject it (constructor / DI) | Replace DB, HTTP, clock in tests |
| Parameter seam | Pass the dependency (or `now`) as a parameter with the old default | Static calls like `DateTime.Now`, `datetime.now()` |
| Subclass and override | Make the awkward method `protected virtual`, override in a test subclass | Java/C# classes you can't restructure yet |
| Link / module seam | Swap a module at import (Python `monkeypatch`, Jest `jest.mock`) | Scripts and modules with global calls |
| DB seam | Synonym / view pointing at old or new object | Stored-procedure rewrites |

## 3. Sprout method / sprout class
New logic goes in a **new**, tested unit; the legacy method gets one line calling it.
```csharp
// legacy method, untouched except one line
public void PostInvoice(Invoice inv)
{
    // ... 300 untested lines ...
    inv.Lines = LineDeduplicator.Dedupe(inv.Lines);   // sprouted, fully tested class
    // ...
}
```

## 4. Wrap method
Keep the old body under a new name, wrap it with before/after behaviour.
```python
def send_fwb(msg):              # public name unchanged
    audit_log(msg)
    return _send_fwb_legacy(msg)

def _send_fwb_legacy(msg):      # old body, moved verbatim
    ...
```

## 5. Branch by abstraction (large internal replacement, one branch in git)
1. Put an interface in front of the old component; route all callers through it.
2. Build the new implementation behind the same interface.
3. Switch per call site or with a feature flag; run both and compare (shadow mode) if you can.
4. Delete the old implementation and, if it adds nothing, the flag.

## 6. Strangler fig (replace a system or module piece by piece)
1. Put a facade/router in front (API gateway route, controller, or a proc that dispatches).
2. Move one capability at a time (e.g. "AWB status query" first, "booking" later).
3. Route that capability to the new code; compare outputs in shadow mode for a period.
4. Remove the old path once traffic and outputs are clean. Repeat.
Good fit: old ASP.NET WebForms / JSP modules, god-procedures behind many callers, monolith → modules.

## 7. Huge files (1,000+ lines)
1. Run `scripts/code_metrics.py` and sort by complexity × lines; start with the worst function that has the most changes in `git log`.
2. Don't read everything: map public entry points and callers first.
3. Plan the split (by responsibility) in the report before moving code; move one unit per step, re-run tests each step.
4. Moves first (no edits), edits second: a pure move is easy to review.
5. Stop at a coherent checkpoint; list the rest as follow-ups rather than one giant diff.

## 8. Regulated / high-risk code (customs, DG, billing, messaging)
- Prefer `tidy` and `restructure` over `minimize`.
- Get sign-off on the characterization set from someone who knows the rules.
- Keep log messages, error codes and message formats (Cargo-IMP / Cargo-XML) byte-identical.
