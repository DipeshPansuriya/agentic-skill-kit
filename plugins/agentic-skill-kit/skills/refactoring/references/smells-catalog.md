# Smells Catalog

Smell → how you spot it → the named refactoring → a small before/after. Snippets are
language-neutral in spirit (C#, Java, Python, TS mixed); see `stack-idioms.md` for idiomatic
per-stack forms. All "after" snippets keep the "before" behaviour.

| # | Smell | Symptom (what `code_metrics.py` or your eye shows) | Refactoring(s) |
|---|---|---|---|
| 1 | Long method | > 40 lines, several "paragraphs" with comments as headings | Extract Method, Decompose Conditional |
| 2 | Large class / god object | Many unrelated fields, 20+ methods, name ends in Manager/Helper/Util | Extract Class, Move Method |
| 3 | Long parameter list | > 4 params, same group passed together | Introduce Parameter Object, Preserve Whole Object |
| 4 | Duplicated code | `duplicate block` lines in the metrics report; copy-paste with one value changed | Extract Method with a parameter, Pull Up |
| 5 | Deep nesting | nesting > 3, "arrow" shape | Guard Clauses, Extract Method |
| 6 | Primitive obsession | AWB / money / weight passed as `string` / `double`, validation repeated | Replace Primitive with Value Object |
| 7 | Feature envy | Method uses another object's getters more than its own fields | Move Method |
| 8 | Shotgun surgery | One change (new status code) touches 6 files | Move Method / Inline Class to one place; lookup table |
| 9 | Dead code | No callers, commented-out blocks, always-false flags | Remove Dead Code (after a repo-wide search) |
| 10 | Magic numbers / strings | `6000`, `0.9`, `'CXL'` in logic | Replace Magic Number with Named Constant / enum |
| 11 | Flag argument | `bool` param that switches behaviour: `Print(x, true)` | Split into two methods (keep the old one delegating) |
| 12 | Comments explaining bad code | `// check if shipment is late and not cancelled and ...` | Extract Method / Rename so the name says it; delete the comment |

## 1. Long method → Extract Method
```python
# before
def close_flight(flight):
    # validate
    if not flight.legs: raise ValueError("no legs")
    if flight.status == "CLOSED": raise ValueError("already closed")
    # totals
    kg = sum(b.kg for b in flight.bookings if b.status != "CXL")
    flight.total_kg = kg
    flight.status = "CLOSED"

# after
def close_flight(flight):
    _ensure_closable(flight)
    flight.total_kg = _live_weight(flight)
    flight.status = "CLOSED"

def _ensure_closable(flight):
    if not flight.legs: raise ValueError("no legs")
    if flight.status == "CLOSED": raise ValueError("already closed")

def _live_weight(flight):
    return sum(b.kg for b in flight.bookings if b.status != "CXL")
```

## 2. Large class → Extract Class
```csharp
// before: BookingManager does pricing, persistence and e-mail
public class BookingManager { public decimal Price(Booking b) {...} public void Save(Booking b) {...} public void Mail(Booking b) {...} }

// after: one reason to change per class; BookingManager kept as a thin facade so callers don't change
public class BookingPricer { public decimal Price(Booking b) {...} }
public class BookingManager(BookingPricer pricer, IBookingRepository repo, IMailer mailer)
{
    public decimal Price(Booking b) => pricer.Price(b);
    public void Save(Booking b) => repo.Save(b);
    public void Mail(Booking b) => mailer.Send(b);
}
```
(`{...}` marks unchanged bodies.) Split in several small steps: move one method, run tests, repeat.

## 3. Long parameter list → Introduce Parameter Object
```java
// before
Quote quote(String origin, String dest, double kg, double cbm, int pcs, boolean dg) { ... }

// after (keep the old overload delegating until all callers move)
record Consignment(String origin, String dest, double kg, double cbm, int pcs, boolean dg) {}
Quote quote(Consignment c) { ... }
Quote quote(String origin, String dest, double kg, double cbm, int pcs, boolean dg) {
    return quote(new Consignment(origin, dest, kg, cbm, pcs, dg));
}
```

## 4. Duplicated code → Extract Method with a parameter
```typescript
// before
const importFee = shipments.filter(s => s.dir === 'IMP').reduce((t, s) => t + s.kg * 0.12, 0);
const exportFee = shipments.filter(s => s.dir === 'EXP').reduce((t, s) => t + s.kg * 0.12, 0);

// after
const HANDLING_RATE = 0.12;
const feeFor = (dir: Direction) =>
  shipments.filter(s => s.dir === dir).reduce((t, s) => t + s.kg * HANDLING_RATE, 0);
const importFee = feeFor('IMP');
const exportFee = feeFor('EXP');
```

## 5. Deep nesting → Guard Clauses
```csharp
// before
if (awb != null) { if (awb.Length == 12) { if (IsOpen(awb)) { Close(awb); } } }

// after
if (awb is null || awb.Length != 12 || !IsOpen(awb)) return;
Close(awb);
```
Check the original for an `else` that throws or returns something different before collapsing.

## 6. Primitive obsession → Value Object
```python
# before: every function that takes an AWB re-validates it
def track(awb: str):
    if not re.fullmatch(r"\d{3}-?\d{8}", awb): raise ValueError(awb)
    ...

# after
@dataclass(frozen=True)
class Awb:
    value: str
    def __post_init__(self):
        if not re.fullmatch(r"\d{3}-?\d{8}", self.value): raise ValueError(self.value)
```
Changing a public signature from `str` to `Awb` is an API change: do it only when asked, or add it
inside the module and keep the `str` entry point.

## 7. Feature envy → Move Method
```java
// before, in InvoiceService: uses only Piece's data
double volumeKg(Piece p) { return p.getL() * p.getW() * p.getH() / 6000.0; }
// after, on Piece (InvoiceService now calls p.volumeKg())
double volumeKg() { return l * w * h / 6000.0; }
```

## 8. Shotgun surgery → one home for the rule
Before: status labels in the API, the PDF and the e-mail each have their own `switch`.
After: one `StatusText` table (see `templates/samples/csharp_after.cs`) used by all three.

## 9. Dead code → Remove
Delete only after: repo-wide search (incl. reflection, DI registration, config, SQL jobs,
scheduled tasks, other repos that call the API). If in doubt, mark `[Obsolete]` / `@Deprecated`
first and list it under follow-ups.

## 10. Magic numbers → Named constants
```sql
-- before
WHERE DATEDIFF(HOUR, ReceivedAt, SYSUTCDATETIME()) > 72
-- after
DECLARE @DwellLimitHours INT = 72;
WHERE DATEDIFF(HOUR, ReceivedAt, SYSUTCDATETIME()) > @DwellLimitHours
```

## 11. Flag argument → Split method
```typescript
// before
render(awb: string, asPdf: boolean) { return asPdf ? this.pdf(awb) : this.html(awb); }
// after: callers say what they mean; keep render() delegating if it is public
renderPdf(awb: string) { return this.pdf(awb); }
renderHtml(awb: string) { return this.html(awb); }
```

## 12. Comment explaining bad code → Rename / Extract
```python
# before
# shipment is late if not delivered and more than 72h since receipt and not cancelled
if s.dlv is None and (now - s.rcv).total_seconds() > 259200 and s.st != "CXL": ...
# after
if is_overdue(s, now): ...

def is_overdue(s, now, limit=timedelta(hours=72)):
    return s.dlv is None and now - s.rcv > limit and s.st != "CXL"
```
Careful: `total_seconds() > 259200` and `now - s.rcv > timedelta(hours=72)` are equal only
for the same types; keep a characterization test on the boundary (exactly 72h).
