# Stack Idioms: Shorter and Clearer, Same Behaviour

Use the idiom only if the repo's language version supports it (check `<LangVersion>`,
`java.version`, `requires-python`, `tsconfig` target, Angular version). Each row notes the
behaviour trap to check before swapping.

## C# (.NET 8, C# 12)
```csharp
// before
public string GetName(Customer c)
{
    if (c == null) throw new ArgumentNullException("c");
    string name;
    if (c.Nick != null) name = c.Nick; else name = c.First + " " + c.Last;
    return name;
}
// after
public string GetName(Customer c)
{
    ArgumentNullException.ThrowIfNull(c);
    return c.Nick ?? $"{c.First} {c.Last}";
}
```
| Before | After | Trap |
|---|---|---|
| `for` loop building a list | `list.ConvertAll(...)` / `.Select(...).ToList()` | `Select` on null throws `ArgumentNullException`, `for`/`ConvertAll` throw `NullReferenceException` |
| `if/else` chain on a code | `switch` expression or `Dictionary` | Dictionary lookup throws on a `null` key; `switch` needs a `_` arm |
| DTO class with props + ctor | `public record BookingDto(string Awb, int Pcs);` | Records have value equality; check code relying on reference equality |
| `new List<string>()` | `[]` (collection expression, C# 12) | Target type must be known |
| Constructor that only assigns fields | Primary constructor `class Svc(IRepo repo)` | Params are captured, not readonly fields |
| `x.ToString("0.0")` | `$"{x:0.0}"` | Both use current culture; don't add `InvariantCulture` in a refactor |
| `try { ... } finally { d.Dispose(); }` | `using var d = ...;` | Dispose moves to end of scope |

## Java (21, Spring Boot 3)
```java
// before
public List<String> openAwbs(List<Booking> bookings) {
    List<String> out = new ArrayList<>();
    for (Booking b : bookings) {
        if (b.getStatus() != null && b.getStatus().equals("OPEN")) {
            out.add(b.getAwb());
        }
    }
    return out;
}
// after
public List<String> openAwbs(List<Booking> bookings) {
    return bookings.stream()
            .filter(b -> "OPEN".equals(b.getStatus()))
            .map(Booking::getAwb)
            .collect(Collectors.toCollection(ArrayList::new));
}
```
| Before | After | Trap |
|---|---|---|
| Loop + `add` | Stream pipeline | `.toList()` is unmodifiable; use `toCollection(ArrayList::new)` if callers mutate |
| POJO with getters/equals/hashCode | `record` | Accessors become `awb()` not `getAwb()`: API change for callers, JPA entities can't be records |
| `switch` statement with `break` | Switch expression `case "ARR" -> ...;` | Must be exhaustive; add `default` with the old fallback |
| `if (o instanceof Foo) { Foo f = (Foo) o; }` | `if (o instanceof Foo f)` | None |
| Null checks chain | `Optional.ofNullable(x).map(...).orElse(d)` only for return values | Don't use `Optional` for fields/params |
| Hand-written constructor injection | Lombok only if the repo already uses it | Don't add dependencies in a refactor |

## Python (3.12)
```python
# before
def active_codes(rows):
    result = []
    for r in rows:
        if r["active"] == True:
            if r["code"] not in result:
                result.append(r["code"])
    return result
# after
def active_codes(rows):
    return list(dict.fromkeys(r["code"] for r in rows if r["active"] == True))  # noqa: E712
```
| Before | After | Trap |
|---|---|---|
| `== True` | truthiness `if x:` | Changes behaviour for `1`, `"Y"`, non-empty lists; keep unless a test proves only bools arrive |
| Manual dedupe keeping order | `dict.fromkeys(...)` | `set()` loses order |
| Index loop `for i in range(len(xs))` | `for x in xs` / `enumerate` / comprehension | None for lists; generators are single-pass |
| `if/elif` ladder on thresholds | Table + `next(...)` or `bisect` | Keep `<` vs `<=` boundaries exactly |
| Class with only `__init__` + fields | `@dataclass(frozen=True, slots=True)` | Frozen blocks mutation; drop `frozen` if code assigns |
| `if/elif` on a value | `match` statement | Only if Python ≥ 3.10 everywhere it runs |
| `os.path.join` chains | `pathlib.Path` | Returns `Path`, not `str`; convert at API boundaries |

## TypeScript / React
```tsx
// before
function AwbList(props: { items: Awb[] }) {
  const [filtered, setFiltered] = useState<Awb[]>([]);
  useEffect(() => { setFiltered(props.items.filter(a => a.status !== 'CXL')); }, [props.items]);
  return <ul>{filtered.map(a => <li key={a.id}>{a.no}</li>)}</ul>;
}
// after: derived data is computed, not stored in state
function AwbList({ items }: { items: Awb[] }) {
  const live = items.filter(a => a.status !== 'CXL');
  return <ul>{live.map(a => <li key={a.id}>{a.no}</li>)}</ul>;
}
```
| Before | After | Trap |
|---|---|---|
| State + effect for derived values | Compute during render (`useMemo` only if measured slow) | First render already shows data (the old one flashed empty); confirm tests expect that |
| `x && x.y && x.y.z` | `x?.y?.z` | Returns `undefined` instead of `false`/`0`/`''` from the short-circuit |
| `a \|\| 'default'` | `a ?? 'default'` | Different for `0`, `''`, `false`: a behaviour change, not a refactor |
| Repeated prop drilling | Composition (`children`) before Context | Context re-renders all consumers |
| String unions duplicated | `as const` array + `typeof arr[number]` | None |

## TypeScript / Angular
```typescript
// before
export class AwbComponent implements OnInit, OnDestroy {
  awb?: Awb;
  private sub?: Subscription;
  constructor(private route: ActivatedRoute, private api: AwbApi) {}
  ngOnInit() {
    this.sub = this.route.paramMap.subscribe(p => {
      this.api.get(p.get('id')!).subscribe(a => this.awb = a);
    });
  }
  ngOnDestroy() { this.sub?.unsubscribe(); }
}
// after (Angular 16+)
export class AwbComponent {
  private route = inject(ActivatedRoute);
  private api = inject(AwbApi);
  awb = toSignal(this.route.paramMap.pipe(switchMap(p => this.api.get(p.get('id')!))));
}
```
| Before | After | Trap |
|---|---|---|
| Nested `subscribe` | `switchMap` / `concatMap` | `switchMap` cancels the in-flight call; the nested version did not. Use `mergeMap` to keep "all complete" semantics. Template must read `awb()` (signal) |
| Manual unsubscribe | `takeUntilDestroyed()` / `async` pipe / `toSignal` | Needs injection context |
| Constructor injection | `inject()` | Only if the repo already uses it; mixing styles hurts readability |
| `*ngIf` / `*ngFor` | `@if` / `@for` (Angular 17+) | `@for` requires `track` |

The Angular "after" is a behavioural change if a user can navigate between ids faster than the
API answers (old: both responses land; new: only the last). Call that out, or use `mergeMap`.
