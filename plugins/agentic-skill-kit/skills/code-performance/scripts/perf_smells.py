#!/usr/bin/env python3
"""Flag heuristic application-performance smells. Python 3 stdlib only.

Languages: .cs .java .py .ts .tsx .js .jsx .mjs
Rules (severity):
  HIGH  sync-over-async      .Result / .Wait() / GetAwaiter().GetResult() (C#)
  HIGH  io-in-loop           DB / HTTP / repository call inside a loop (N+1, chatty I/O)
  HIGH  blocking-in-async    time.sleep / requests.* / sync DB call inside async def (Python)
  HIGH  async-foreach        .forEach(async ...) does not await (JS/TS)
  MED   await-in-loop        sequential await inside a loop (consider bounded concurrency / batch)
  MED   string-concat-loop   string += inside a loop (use StringBuilder / join / array push)
  MED   linear-lookup-loop   .Contains/.includes/indexOf/Any/find/`in list` inside a loop -> O(n*m)
  MED   regex-in-loop        new Regex / Pattern.compile / re.compile / new RegExp inside a loop
  MED   sleep-in-code        Thread.Sleep / Thread.sleep / time.sleep outside tests
  MED   select-star          SELECT * in a string literal (over-fetching)
  MED   filter-in-memory     ToList()/findAll() before Where/filter (loads whole table)
  MED   pandas-iterrows      DataFrame.iterrows() (vectorize instead)
  LOW   regex-per-call       regex compiled inside a function body (hoist to static / module level)
  LOW   log-in-loop          console.log / print / Console.WriteLine / println / logger.* inside a loop

Heuristic, line-based: expect false positives (e.g. .Contains on a HashSet, .Result on a
non-Task type, `in` on a set) and false negatives (lazy-loading N+1, calls via helpers).
Confirm every finding with a profiler or by reading the code.

Usage:
  python3 perf_smells.py src/                  # scan a folder recursively
  python3 perf_smells.py a.cs b.py --min MED   # only MED and HIGH
Exit code: 1 if any HIGH, else 0.
"""
import re
import sys
from pathlib import Path

EXTS = {".cs", ".java", ".py", ".ts", ".tsx", ".js", ".jsx", ".mjs"}
SKIP_DIRS = {"node_modules", ".git", "bin", "obj", "target", "dist", "build", ".venv", "venv", "__pycache__"}
SEV = {"LOW": 0, "MED": 1, "HIGH": 2}

IO = {
    "cs": re.compile(r"SaveChanges(Async)?\s*\(|Execute(Reader|Scalar|NonQuery)(Async)?\s*\(|"
                     r"\b_?(context|db|dbContext|ctx)\.\w+|\b_?\w*[Rr]epo(sitory)?\.\w+\s*\(|"
                     r"\.(Get|Post|Put|Patch|Delete|Send)(Async|FromJsonAsync|AsJsonAsync)\s*\(|"
                     r"\.(Query|QueryFirst\w*|QuerySingle\w*|Execute)(Async)?\s*[<(]"),
    "java": re.compile(r"execute(Query|Update)?\s*\(|jdbcTemplate\.|restTemplate\.|webClient\.|restClient\.|"
                       r"entityManager\.(find|createQuery|persist|merge)|\b\w*[Rr]epo(sitory)?\.\w+\s*\(|"
                       r"\.findBy\w*\s*\(|\.findById\s*\("),
    "py": re.compile(r"\brequests\.(get|post|put|patch|delete|request)\s*\(|\bhttpx\.\w+\s*\(|"
                     r"\bsession\.(query|get|execute|scalars?)\s*\(|\bcursor\.execute\w*\s*\(|"
                     r"\.objects\.(get|filter|create|all)\s*\(|\burlopen\s*\(|\b\w*_?repo(sitory)?\.\w+\s*\(|"
                     r"\bclient\.(get|post|put|delete)\s*\("),
    "js": re.compile(r"\bfetch\s*\(|\baxios(\.\w+)?\s*\(|\bhttp\.(get|post|put|patch|delete)\s*\(|"
                     r"\bthis\.http\.\w+\s*\(|\b(db|pool|client|prisma|knex)\.\w+.*\(|\.query\s*\(|\b\w*[Rr]epo(sitory)?\.\w+\s*\("),
}
LOOP = {
    "cs": re.compile(r"^\s*(\}\s*)?(for|foreach|while)\s*\(|\.ForEach\s*\(|Parallel\.ForEach(Async)?\s*\(|^\s*do\s*(\{|$)"),
    "java": re.compile(r"^\s*(\}\s*)?(for|while)\s*\(|\.forEach\s*\(|^\s*do\s*(\{|$)"),
    "js": re.compile(r"^\s*(\}\s*)?(for|while)\s*\(|^\s*for\s+await\s*\(|\.forEach\s*\(|\.map\s*\(\s*(async\s*)?\(?\w*\)?\s*=>|^\s*do\s*(\{|$)"),
}
LOOKUP = {
    "cs": re.compile(r"\.(Contains|IndexOf|Any|Where|First|FirstOrDefault|Single|SingleOrDefault|Find)\s*\("),
    "java": re.compile(r"\.(contains|indexOf|lastIndexOf)\s*\(|\.stream\(\)\s*\.\s*(filter|anyMatch)\s*\("),
    "js": re.compile(r"\.(includes|indexOf|lastIndexOf|find|findIndex|filter|some)\s*\("),
}
REGEX = {
    "cs": re.compile(r"\bnew\s+Regex\s*\("),
    "java": re.compile(r"\bPattern\.compile\s*\("),
    "py": re.compile(r"\bre\.compile\s*\("),
    "js": re.compile(r"\bnew\s+RegExp\s*\("),
}
LOG = {
    "cs": re.compile(r"\bConsole\.Write(Line)?\s*\(|\b_?logger\.Log\w*\s*\("),
    "java": re.compile(r"System\.(out|err)\.print(ln)?\s*\(|\b(log|logger|LOG|LOGGER)\.(debug|info|trace)\s*\("),
    "py": re.compile(r"^\s*print\s*\(|\b(log|logger|logging)\.(debug|info)\s*\("),
    "js": re.compile(r"\bconsole\.(log|debug|info)\s*\("),
}
SLEEP = re.compile(r"\bThread\.[Ss]leep\s*\(|\btime\.sleep\s*\(")
SYNC_OVER_ASYNC = re.compile(r"(?:\)|\b\w*[Tt]ask\w*)\.Result\b(?!\s*[=(])|\.Wait\s*\(\s*\)|GetAwaiter\s*\(\s*\)\s*\.\s*GetResult\s*\(")
CONCAT = re.compile(r"\+=\s*(\$|@|f|rf|fr)?[\"'`]|\+=.*\+\s*(\$|f)?[\"'`]|\+=\s*(str|String\.valueOf)\s*\(|"
                    r"\+=.*\.ToString\s*\(|\b(?P<v>\w+)\s*=\s*(?P=v)\s*\+\s*[\"'`$]")
SELECT_STAR = re.compile(r"""(?i)["'`$@]\s*select\s+\*\s+from\b|\bselect\s+\*\s+from\b.*["'`]""")
FILTER_MEM = re.compile(r"\.(ToList|ToArray|AsEnumerable)\s*\(\s*\)\s*\.\s*(Where|Select|First\w*|Any|Count)\s*\(|"
                        r"\.findAll\s*\(\s*\)\s*\.\s*stream\s*\(\s*\)\s*\.\s*filter")
AWAIT = re.compile(r"\bawait\b")
ASYNC_FOREACH = re.compile(r"\.forEach\s*\(\s*async\b")
PY_LOOP = re.compile(r"^\s*(async\s+)?(for|while)\b.*:\s*(#.*)?$")
PY_COMPREHENSION = re.compile(r"[\[({].*\bfor\b.+\bin\b.+[\])}]")
PY_DEF = re.compile(r"^(\s*)(async\s+)?def\s+\w+")
PY_BLOCKING = re.compile(r"\btime\.sleep\s*\(|\brequests\.\w+\s*\(|\burlopen\s*\(|\bcursor\.execute\s*\(|\bsession\.(query|execute)\s*\(")
PY_IN_LIST = re.compile(r"\bif\b.*\b(not\s+)?in\s+(?!range\b|\(|\{)([a-z_][\w.]*)\s*:")
SET_LIKE = re.compile(r"(set|dict|dictionary|map|lookup|index|keys|cache|by_?\w+|seen)$", re.I)  # name suggests O(1) lookup
ITERROWS = re.compile(r"\.iterrows\s*\(")
STR_LIT = re.compile(r"""(\$@|@\$|\$|@|f|r|rb|b|fr|rf)?("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|`(?:\\.|[^`\\])*`)""")

MSG = {
    "sync-over-async": "Blocks a thread pool thread (starvation/deadlock risk): make the call chain async and await it",
    "io-in-loop": "DB/HTTP call per iteration (N+1 / chatty I/O): batch (IN / bulk / saveAll), prefetch into a dict, or join",
    "blocking-in-async": "Blocking call inside async def stalls the event loop: use asyncio.sleep / httpx.AsyncClient / async driver / to_thread",
    "async-foreach": "forEach ignores returned promises: use for...of with await, or Promise.all with a concurrency limit",
    "await-in-loop": "Sequential awaits add latencies: if independent, run with bounded concurrency (Task.WhenAll / Promise.all / gather + semaphore)",
    "string-concat-loop": "String += in a loop copies the string each time (O(n^2)): use StringBuilder / ''.join / array.join",
    "linear-lookup-loop": "Linear search inside a loop is O(n*m): build a HashSet/Set/dict once before the loop (verify the type)",
    "regex-in-loop": "Regex compiled on every iteration: hoist to a static readonly / module-level compiled pattern",
    "sleep-in-code": "Sleep blocks a worker thread: use a scheduler, retry policy with backoff, or async delay",
    "select-star": "SELECT * over-fetches columns and breaks covering indexes: select only needed columns",
    "filter-in-memory": "Materializes the whole set then filters in memory: filter/project in the query (IQueryable / repository method)",
    "pandas-iterrows": "iterrows is row-by-row Python: vectorize with column ops, np.where, merge, or groupby",
    "regex-per-call": "Regex compiled on every call: hoist to a static readonly field / module constant if the function is hot",
    "log-in-loop": "Logging per iteration in a hot path costs I/O and allocations: log a summary or guard with level checks",
}
SEVERITY = {
    "sync-over-async": "HIGH", "io-in-loop": "HIGH", "blocking-in-async": "HIGH", "async-foreach": "HIGH",
    "await-in-loop": "MED", "string-concat-loop": "MED", "linear-lookup-loop": "MED", "regex-in-loop": "MED",
    "sleep-in-code": "MED", "select-star": "MED", "filter-in-memory": "MED", "pandas-iterrows": "MED",
    "regex-per-call": "LOW", "log-in-loop": "LOW",
}


def lang_of(path):
    ext = path.suffix.lower()
    return {".cs": "cs", ".java": "java", ".py": "py"}.get(ext, "js")


def blank_strings(code):
    """Keep quotes and prefixes, blank string contents, so braces/keywords inside strings are ignored."""
    return STR_LIT.sub(lambda m: (m.group(1) or "") + m.group(2)[0] * 2, code)


def is_test(path):
    n = path.name.lower()
    parts = [p.lower() for p in path.parts]
    return bool(re.search(r"(^|[._-])(tests?|spec)([._-]|$)|^test_|(tests?|spec)\.\w+$", n)) \
        or any(p in {"test", "tests", "__tests__", "e2e"} or p.endswith("tests") for p in parts)


GENERATED = re.compile(r"\.(gen|g|generated|designer)\.\w+$|\.min\.js$", re.I)


def check_line(lang, raw, code, in_loop, in_func, in_async, add):
    """Apply rules to one line. `code` has comments removed and string contents blanked."""
    if lang == "cs" and SYNC_OVER_ASYNC.search(code):
        add("sync-over-async")
    if SELECT_STAR.search(raw):
        add("select-star")
    if FILTER_MEM.search(code):
        add("filter-in-memory")
    if lang == "py" and ITERROWS.search(code):
        add("pandas-iterrows")
    if lang == "js" and ASYNC_FOREACH.search(code):
        add("async-foreach")
    if SLEEP.search(code):
        add("blocking-in-async" if (lang == "py" and in_async) else "sleep-in-code")
    elif lang == "py" and in_async and PY_BLOCKING.search(code):
        add("blocking-in-async")
    regex_hit = REGEX[lang].search(code)
    if in_loop:
        full_loop = in_loop != "comp"  # "comp" = Python comprehension/generator on this line only
        io = IO[lang].search(code)
        if io:
            add("io-in-loop")
        elif full_loop and AWAIT.search(code):
            add("await-in-loop")
        if full_loop and CONCAT.search(code):
            add("string-concat-loop")
        if not io:
            if lang == "py":
                m = PY_IN_LIST.search(code)
                substring = re.search(r"[\"']\s+(not\s+)?in\s", code)  # "x" in text is a str search
                if (m and not substring and not SET_LIKE.search(m.group(2))) or re.search(r"\w\.index\s*\(", code):
                    add("linear-lookup-loop")
            else:
                m = LOOKUP[lang].search(code)
                receiver = re.search(r"(\w+)\s*$", code[:m.start()]) if m else None
                if m and not (receiver and SET_LIKE.search(receiver.group(1))):
                    add("linear-lookup-loop")
        if regex_hit:
            add("regex-in-loop")
        if full_loop and LOG[lang].search(code):
            add("log-in-loop")
    elif regex_hit and in_func and not re.search(r"\bstatic\b|\bfinal\b|^\s*(const|let|var)\s+[A-Z_]+\s*=", code):
        add("regex-per-call")


def scan_python(path, lines, report):
    loops, funcs = [], []  # stacks of indent levels / (indent, is_async)
    for no, raw in enumerate(lines, 1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        while loops and indent <= loops[-1]:
            loops.pop()
        while funcs and indent <= funcs[-1][0]:
            funcs.pop()
        code = blank_strings(raw.split(" #")[0])
        header = PY_LOOP.match(code)
        d = PY_DEF.match(code)
        in_loop = bool(loops) or ("comp" if PY_COMPREHENSION.search(code) and not header else False)
        in_func, in_async = bool(funcs), bool(funcs and funcs[-1][1])
        add = report(no, raw)
        if not d:
            check_line("py", raw, code, in_loop, in_func, in_async, add)
        if header:  # body on the same line as the loop header
            after = code.rstrip().split(":", 1)[1] if ":" in code.rstrip()[:-1] else ""
            if after.strip():
                check_line("py", raw, after, True, in_func, in_async, add)
        if header:
            loops.append(indent)
        if d:
            funcs.append((indent, bool(d.group(2))))


def scan_braces(path, lang, lines, report):
    depth, loop_stack, func_depth = 0, [], 0
    pending, in_block_comment = False, False
    for no, raw in enumerate(lines, 1):
        line = raw
        if in_block_comment:
            if "*/" not in line:
                continue
            line, in_block_comment = line.split("*/", 1)[1], False
        code = blank_strings(line)
        code = re.sub(r"/\*.*?\*/", "", code)
        if "/*" in code:
            code, in_block_comment = code.split("/*", 1)[0], True
        code = re.sub(r"//.*$", "", code)
        if not code.strip():
            continue
        header = LOOP[lang].search(code)
        is_do_while_tail = bool(re.match(r"^\s*\}\s*while\s*\(", code))
        single_stmt = pending and not code.lstrip().startswith("{")
        in_loop = bool(loop_stack) or single_stmt
        in_func = depth >= 2 or (lang == "js" and depth >= 1)
        add = report(no, raw)
        check_line(lang, raw, code, in_loop, in_func, False, add)
        if header and not is_do_while_tail:
            tail = code[header.end():]
            body = tail.split("{", 1)[1] if "{" in tail else (tail if tail.rstrip().endswith(";") else "")
            if body.strip():  # loop body on the same line as the header
                check_line(lang, raw, body, True, in_func, False, add)
        if single_stmt:
            pending = False
        opened_after_header = False
        for i, ch in enumerate(code):
            if ch == "{":
                depth += 1
                if pending or (header and not is_do_while_tail and i >= header.start()):
                    loop_stack.append(depth)
                    pending = False
                    opened_after_header = True
            elif ch == "}":
                if loop_stack and depth == loop_stack[-1]:
                    loop_stack.pop()
                depth = max(0, depth - 1)
        if header and not is_do_while_tail and not opened_after_header and not code.rstrip().endswith(";"):
            pending = True  # body (a `{` block or a single statement) starts on the next line


def scan(path):
    lang = lang_of(path)
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as e:
        print(f"{path}: cannot read ({e})", file=sys.stderr)
        return []
    findings = []
    test_file = is_test(path)

    def report(no, raw):
        seen = set()

        def add(rule):
            if rule in seen or (test_file and rule == "sleep-in-code"):
                return
            seen.add(rule)
            findings.append((str(path), no, SEVERITY[rule], rule, MSG[rule], raw.strip()[:120]))
        return add

    if lang == "py":
        scan_python(path, lines, report)
    else:
        scan_braces(path, lang, lines, report)
    out = []
    for file, no, sev, rule, msg, snip in findings:
        if rule == "sync-over-async" and any("Task.WhenAll" in lines[i] for i in range(max(0, no - 11), no - 1)):
            sev, msg = "LOW", "Verify: .Result after await Task.WhenAll is safe (already completed); prefer await for clarity"
        elif test_file and sev != "LOW":
            sev, msg = "LOW", "(test code) " + msg
        out.append((file, no, sev, rule, msg, snip))
    return out


def iter_files(args):
    for a in args:
        p = Path(a)
        if p.is_dir():
            for f in sorted(p.rglob("*")):
                if f.is_file() and f.suffix.lower() in EXTS and not SKIP_DIRS.intersection(f.parts) and not GENERATED.search(f.name):
                    yield f
        elif p.is_file():
            yield p
        else:
            print(f"{a}: not found", file=sys.stderr)


def main(argv):
    minimum = "LOW"
    if "--min" in argv:
        i = argv.index("--min")
        minimum = argv[i + 1].upper() if i + 1 < len(argv) else "LOW"
        argv = argv[:i] + argv[i + 2:]
    if not argv or minimum not in SEV:
        sys.exit(__doc__)
    all_findings = []
    files = list(iter_files(argv))
    files = [f for f in files if f.resolve() != Path(__file__).resolve()]  # skip own rule definitions
    for f in files:
        all_findings += [x for x in scan(f) if SEV[x[2]] >= SEV[minimum]]
    all_findings.sort(key=lambda x: (-SEV[x[2]], x[0], x[1]))
    for file, no, sev, rule, msg, snippet in all_findings:
        print(f"{file}:{no}  {sev:<4}  {rule:<19} {msg}\n    > {snippet}")
    counts = {s: sum(1 for x in all_findings if x[2] == s) for s in ("HIGH", "MED", "LOW")}
    print(f"\nScanned {len(files)} file(s): {counts['HIGH']} HIGH, {counts['MED']} MED, {counts['LOW']} LOW. "
          "Heuristic - confirm each finding with a profiler or by reading the code.")
    return 1 if counts["HIGH"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
