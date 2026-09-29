#!/usr/bin/env python3
"""Heuristic SQL linter (PostgreSQL / SQL Server / ANSI). Python 3 stdlib only.

Flags common correctness and performance smells with line numbers:
  ERROR  update-no-where / delete-no-where / destructive-ddl
  WARN   select-star, leading-wildcard-like, non-sargable, not-in-subquery,
         implicit-join, dynamic-sql-concat
  INFO   order-by-no-limit, exec-string

Heuristic: treat findings as leads to confirm in the code, not verdicts.

Usage:
  python3 sql_lint.py query.sql            # lint a file
  cat query.sql | python3 sql_lint.py      # lint stdin (or pass "-")
  python3 sql_lint.py query.sql --min WARN # hide INFO
Exit code: 1 if any ERROR, else 0.
"""
import bisect
import re
import sys

SEV_ORDER = {"INFO": 0, "WARN": 1, "ERROR": 2}
I = re.I
STMT_START = re.compile(
    r"(?:SELECT|INSERT|UPDATE|DELETE|MERGE|WITH|EXEC|EXECUTE|DECLARE|BEGIN|IF|WHILE|"
    r"CREATE|ALTER|DROP|TRUNCATE|GO|RETURN|PRINT|"
    r"SET\s+(?:@|NOCOUNT|XACT_ABORT|STATISTICS|LOCK_TIMEOUT|TRANSACTION))\b", I)
FUNCS = (r"YEAR|MONTH|DAY|LOWER|UPPER|TRIM|LTRIM|RTRIM|CONVERT|CAST|ISNULL|COALESCE|NVL|"
         r"IFNULL|DATEPART|DATEADD|DATEDIFF|DATE_TRUNC|DATE_PART|TO_CHAR|TO_DATE|SUBSTRING|"
         r"SUBSTR|LEFT|RIGHT|DATE|EXTRACT|FORMAT|LEN|LENGTH|REPLACE|ABS|ROUND|FLOOR")
NON_SARG = re.compile(
    r"(?:\bWHERE|\bAND|\bOR|\bON|\bNOT|\()\s*(" + FUNCS + r")\s*\(([^()]*(?:\([^()]*\)[^()]*)*)\)"
    r"\s*(?:=|<>|!=|<=|>=|<|>|\bLIKE\b|\bIN\b|\bBETWEEN\b)", I)
NOT_COLUMN = re.compile(
    r"^(?:year|yy|yyyy|quarter|qq|month|mm|m|dayofyear|dy|day|dd|d|week|wk|ww|weekday|dw|"
    r"hour|hh|minute|mi|n|second|ss|s|millisecond|ms|from|as|date|datetime|datetime2|time|"
    r"timestamp|timestamptz|varchar|nvarchar|char|nchar|int|bigint|decimal|numeric|text|"
    r"null|and|or|using|epoch|dow|doy|isodow|utc)$", I)


def mask(src):
    """Return (code, nostr, strings): comments blanked; string contents blanked in nostr."""
    code, nostr, strings = list(src), list(src), []
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        if src.startswith("--", i):
            j = src.find("\n", i)
            j = n if j == -1 else j
            for k in range(i, j):
                code[k] = nostr[k] = " "
            i = j
        elif src.startswith("/*", i):
            j = src.find("*/", i + 2)
            j = n if j == -1 else j + 2
            for k in range(i, j):
                if src[k] != "\n":
                    code[k] = nostr[k] = " "
            i = j
        elif c == "'":
            j = i + 1
            while j < n:
                if src[j] == "'" and j + 1 < n and src[j + 1] == "'":
                    j += 2
                    continue
                if src[j] == "'":
                    break
                j += 1
            j = min(j, n - 1)
            strings.append((i, j + 1, src[i + 1:j]))
            for k in range(i + 1, j):
                if src[k] != "\n":
                    nostr[k] = " "
            i = j + 1
        else:
            i += 1
    return "".join(code), "".join(nostr), strings


def split_statements(nostr):
    """Split on ';' and on statement keywords at line start, both at paren depth 0."""
    bounds, start, depth, i, n = [], 0, 0, 0, len(nostr)
    while i < n:
        c = nostr[i]
        if c == "(":
            depth += 1
        elif c == ")":
            depth = max(0, depth - 1)
        elif c == ";" and depth == 0:
            bounds.append((start, i))
            start = i + 1
        elif c == "\n" and depth == 0:
            m = re.match(r"[ \t]*", nostr[i + 1:])
            pos = i + 1 + m.end()
            if STMT_START.match(nostr, pos) and nostr[start:i].strip():
                bounds.append((start, i))
                start = pos
        i += 1
    bounds.append((start, n))
    return [(s, e) for s, e in bounds if nostr[s:e].strip()]


def depth0_mask(seg):
    """Blank everything inside parentheses so only top-level clauses remain."""
    out, depth = [], 0
    for ch in seg:
        if ch == "(":
            depth += 1
            out.append(" ")
        elif ch == ")":
            depth = max(0, depth - 1)
            out.append(" ")
        else:
            out.append(ch if depth == 0 else " ")
    return "".join(out)


def lint(src):
    code, nostr, strings = mask(src)
    nl = [i for i, ch in enumerate(src) if ch == "\n"]
    line = lambda pos: bisect.bisect_right(nl, pos - 1) + 1  # noqa: E731
    out = []

    def add(pos, sev, rule, msg):
        out.append((line(pos), sev, rule, msg))

    for s, e in split_statements(nostr):
        seg = nostr[s:e]
        top = depth0_mask(seg)
        first = re.match(r"\s*(\w+)", seg)
        kw = first.group(1).upper() if first else ""

        for m in re.finditer(r"\bSELECT\s+(?:ALL\s+|DISTINCT\s+|TOP\s*\(?\s*\d+\s*\)?\s*(?:PERCENT\s+)?)*(?:\w+\.)?\*", seg, I):
            if not re.search(r"\bEXISTS\s*\(\s*$", nostr[max(0, s + m.start() - 40):s + m.start()], I):
                add(s + m.start(), "WARN", "select-star", "SELECT * : list columns explicitly (plan stability, covering indexes, schema drift)")

        if kw in ("UPDATE", "DELETE") and not re.search(r"\bWHERE\b", seg, I):
            if kw == "DELETE" or re.search(r"\bSET\b", seg, I):
                add(s + first.start(1), "ERROR", kw.lower() + "-no-where",
                    f"{kw} without WHERE affects every row: confirm intent, wrap in a transaction with a verification SELECT")
        m = re.match(r"\s*(TRUNCATE\b|DROP\s+(?:TABLE|DATABASE|SCHEMA|INDEX)\b)", seg, I)
        if m:
            add(s + m.start(1), "ERROR", "destructive-ddl", f"{m.group(1).split()[0].upper()} is destructive: requires explicit confirmation and a rollback plan")

        for m in NON_SARG.finditer(seg):
            args = re.sub(r"'[^']*'|[@$:]\w+|\b\d+(?:\.\d+)?\b", " ", m.group(2))
            idents = [t for t in re.findall(r"[A-Za-z_\[\"][\w.\]\"]*", args) if not NOT_COLUMN.match(t.strip('[]"'))]
            if idents:
                add(s + m.start(1), "WARN", "non-sargable",
                    f"{m.group(1).upper()}({idents[0]}) in a predicate prevents an index seek: rewrite as a range / compare the raw column, or use an expression index")

        for m in re.finditer(r"\bNOT\s+IN\s*\(\s*SELECT\b", seg, I):
            add(s + m.start(), "WARN", "not-in-subquery", "NOT IN (SELECT ...) returns no rows if the subquery yields a NULL: use NOT EXISTS")

        for m in re.finditer(r"\bFROM\s+[\w.\[\]\"#]+(?:\s+(?:AS\s+)?(?!WHERE\b|JOIN\b|INNER\b|LEFT\b|RIGHT\b|FULL\b|CROSS\b|ON\b|GROUP\b|ORDER\b)\w+)?\s*,\s*[\w\[\]\"#]", top, I):
            add(s + m.start(), "WARN", "implicit-join", "Comma join in FROM: use explicit JOIN ... ON (a lost predicate becomes a cartesian product)")

        if kw in ("SELECT", "WITH"):
            ob = re.search(r"\bORDER\s+BY\b", top, I)
            if ob and not re.search(r"\b(LIMIT|TOP|FETCH\s+(FIRST|NEXT)|OFFSET)\b", seg, I) and not re.search(r"\bINTO\b|\bCOUNT\s*\(", top, I):
                add(s + ob.start(), "INFO", "order-by-no-limit", "ORDER BY without LIMIT/TOP/FETCH: full sort of a potentially large result; page with keyset + LIMIT if large")

    for m in re.finditer(r"\bLIKE\s+N?'%", code, I):
        add(m.start(), "WARN", "leading-wildcard-like", "LIKE '%...' cannot use a B-tree index: consider trigram (pg_trgm GIN), full-text, or a prefix search")
    for m in re.finditer(r"\bLIKE\s+(?:CONCAT\s*\(\s*N?'%'|N?'%'\s*(?:\+|\|\|))", code, I):
        add(m.start(), "WARN", "leading-wildcard-like", "Leading wildcard built by concatenation cannot use a B-tree index")

    kwre = re.compile(r"\b(SELECT|INSERT|UPDATE|DELETE|WHERE|FROM|EXEC|VALUES|ORDER\s+BY)\b", I)
    seen = set()
    for a, b, text in strings:
        if not kwre.search(text):
            continue
        after = nostr[b:b + 6].lstrip()
        before = nostr[max(0, a - 6):a].rstrip()
        if before.endswith("N"):
            before = before[:-1].rstrip()
        if after.startswith(("+", "||")) or before.endswith(("+", "||")):
            ln = line(a)
            if ln not in seen:
                seen.add(ln)
                add(a, "WARN", "dynamic-sql-concat", "SQL text built by string concatenation: injection risk. Use sp_executesql with parameters (T-SQL) or format() with %I/%L / USING (PL/pgSQL)")
    for m in re.finditer(r"\bEXEC(?:UTE)?\s*\(\s*@\w+", nostr, I):
        add(m.start(), "INFO", "exec-string", "EXEC(@sql): prefer sp_executesql with typed parameters (plan reuse, no injection)")

    return sorted(out, key=lambda r: (r[0], -SEV_ORDER[r[1]]))


def main(argv):
    args = [a for a in argv[1:]]
    min_sev = "INFO"
    if "--min" in args:
        k = args.index("--min")
        min_sev = args[k + 1].upper() if k + 1 < len(args) else "INFO"
        del args[k:k + 2]
    if args and args[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    path = args[0] if args else "-"
    src = sys.stdin.read() if path == "-" else open(path, encoding="utf-8-sig").read()
    name = "stdin" if path == "-" else path
    findings = [f for f in lint(src) if SEV_ORDER[f[1]] >= SEV_ORDER.get(min_sev, 0)]
    for ln, sev, rule, msg in findings:
        print(f"{name}:{ln}: {sev:<5} [{rule}] {msg}")
    counts = {k: sum(1 for f in findings if f[1] == k) for k in ("ERROR", "WARN", "INFO")}
    print(f"-- {counts['ERROR']} error(s), {counts['WARN']} warning(s), {counts['INFO']} info")
    return 1 if counts["ERROR"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
