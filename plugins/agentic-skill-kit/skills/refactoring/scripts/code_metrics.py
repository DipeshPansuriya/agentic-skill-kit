#!/usr/bin/env python3
"""Maintainability metrics for refactoring (Python 3 stdlib only).

Scans .py .cs .java .ts .tsx .js .sql files (or folders of them) and reports:
  per function / method / procedure: lines, max nesting depth, parameter count,
      approximate cyclomatic complexity (and cursor use for SQL)
  per file: total lines, code lines, functions, duplicate blocks (>= 6 identical
      normalized lines, repeated anywhere in the scanned set)
Flags: function > 40 lines, nesting > 3, params > 4, complexity > 10, SQL cursor.

Python is parsed with `ast` (exact). C#, Java, TS/JS use brace heuristics and SQL
uses keyword heuristics (BEGIN/END, IF, WHILE, WHEN, CURSOR): treat those numbers as
approximate and compare like with like (before vs after of the same code).

Usage:
  python3 code_metrics.py src/Billing.cs                   # table report
  python3 code_metrics.py src/ --json                      # JSON
  python3 code_metrics.py --compare before.py after.py     # deltas (files or dirs)
  python3 code_metrics.py --compare old/ new/ --json
Exit code: 0 always (metrics are information, not a gate).
"""
import argparse
import ast
import hashlib
import json
import re
import sys
from pathlib import Path

EXTS = {".py", ".cs", ".java", ".ts", ".tsx", ".js", ".sql"}
LIMITS = {"lines": 40, "nesting": 3, "params": 4, "complexity": 10}
DUP_WINDOW = 6
SKIP_DIRS = {".git", "node_modules", "bin", "obj", "target", "dist", "build", "__pycache__", ".venv", "venv"}

# ---------------------------------------------------------------- Python (ast)
BRANCH_NODES = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.ExceptHandler, ast.IfExp, ast.Assert)
NEST_NODES = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.With, ast.AsyncWith, ast.Try)
if hasattr(ast, "match_case"):
    BRANCH_NODES += (ast.match_case,)
    NEST_NODES += (ast.Match,)
if hasattr(ast, "TryStar"):
    NEST_NODES += (ast.TryStar,)
FUNC_NODES = (ast.FunctionDef, ast.AsyncFunctionDef)


def _py_nesting(node, depth=0):
    best = depth
    for child in ast.iter_child_nodes(node):
        if isinstance(child, FUNC_NODES + (ast.ClassDef, ast.Lambda)):
            continue  # nested defs are measured on their own
        # `elif` is an If inside orelse: same visual level, do not add depth
        is_elif = isinstance(node, ast.If) and isinstance(child, ast.If) and child in node.orelse and len(node.orelse) == 1
        step = 1 if isinstance(child, NEST_NODES) and not is_elif else 0
        best = max(best, _py_nesting(child, depth + step))
    return best


def _py_complexity(func):
    score = 1
    stack = list(ast.iter_child_nodes(func))
    while stack:
        n = stack.pop()
        if isinstance(n, FUNC_NODES + (ast.ClassDef,)):
            continue
        if isinstance(n, BRANCH_NODES):
            score += 1
        elif isinstance(n, ast.BoolOp):
            score += len(n.values) - 1
        elif isinstance(n, ast.comprehension):
            score += 1 + len(n.ifs)
        stack.extend(ast.iter_child_nodes(n))
    return score


def python_functions(text):
    try:
        tree = ast.parse(text)
    except SyntaxError as e:
        return [], f"syntax error line {e.lineno}: {e.msg}"
    out = []

    def visit(node, prefix=""):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef):
                visit(child, f"{prefix}{child.name}.")
            elif isinstance(child, FUNC_NODES):
                a = child.args
                params = [p.arg for p in a.posonlyargs + a.args + a.kwonlyargs]
                params = [p for p in params if p not in ("self", "cls")]
                params += [x.arg for x in (a.vararg, a.kwarg) if x]
                start = min([child.lineno] + [d.lineno for d in child.decorator_list])
                out.append({
                    "name": prefix + child.name, "line": child.lineno,
                    "lines": child.end_lineno - start + 1,
                    "nesting": _py_nesting(child), "params": len(params),
                    "complexity": _py_complexity(child),
                })
                visit(child, f"{prefix}{child.name}.")
            else:
                visit(child, prefix)

    visit(tree)
    return out, None


# ------------------------------------------------- C# / Java / TS / JS (braces)
KEYWORDS = {"if", "for", "foreach", "while", "switch", "catch", "using", "lock", "fixed", "return",
            "new", "function", "else", "do", "try", "finally", "synchronized", "typeof", "sizeof",
            "nameof", "await", "throw", "yield", "when", "checked", "unchecked", "super", "this", "base"}
DECL_WORDS = {"class", "record", "struct", "interface", "enum", "new", "extends", "implements"}
PARAMS = r"\(((?:[^()]|\([^()]*\))*)\)"
FUNC_RE = re.compile(
    r"\b([A-Za-z_$][\w$]*)\s*(?:<[^<>(){};]*(?:<[^<>]*>[^<>(){};]*)*>)?\s*" + PARAMS +
    r"\s*(?::\s*[^={};]+?)?\s*(?:throws\s+[\w.,\s]+?)?\s*(?:where\s+[^{;]+?)?\s*(=>\s*)?\{")
ARROW_RE = re.compile(
    r"\b([A-Za-z_$][\w$]*)\s*(?::\s*[^=;{}]+?)?=\s*(?:async\s+)?" + PARAMS +
    r"\s*(?::\s*[^={};]+?)?\s*=>\s*\{")
# expression-bodied members / arrows:  int Twice(int x) => x * 2;   const f = (a) => a + 1;
EXPR_FUNC_RE = re.compile(r"\b([A-Za-z_$][\w$]*)\s*(?:<[^<>(){};]*>)?\s*" + PARAMS + r"\s*(?::\s*[^={};]+?)?\s*=>\s*(?=[^\s{])")
EXPR_ARROW_RE = re.compile(r"\b([A-Za-z_$][\w$]*)\s*(?::\s*[^=;{}]+?)?=\s*(?:async\s+)?" + PARAMS +
                           r"\s*(?::\s*[^={};]+?)?\s*=>\s*(?=[^\s{])")
CONTROL_RE = re.compile(r"\b(?:if|for|foreach|while|case|catch)\b|&&|\|\||\s\?\s")


def strip_code(text):
    """Blank out comments and string/char literals, keeping newlines and length."""
    out, i, n = [], 0, len(text)
    while i < n:
        c, nxt = text[i], text[i + 1] if i + 1 < n else ""
        if c == "/" and nxt == "/":
            j = text.find("\n", i)
            j = n if j == -1 else j
            out.append(" " * (j - i)); i = j
        elif c == "/" and nxt == "*":
            j = text.find("*/", i + 2)
            j = n if j == -1 else j + 2
            out.append(re.sub(r"[^\n]", " ", text[i:j])); i = j
        elif c in "\"'`":
            verbatim = c == '"' and i > 0 and text[i - 1] == "@"
            j = i + 1
            while j < n:
                if text[j] == "\\" and not verbatim:
                    j += 2; continue
                if text[j] == c:
                    if verbatim and j + 1 < n and text[j + 1] == '"':
                        j += 2; continue
                    break
                if text[j] == "\n" and c != "`" and not verbatim:
                    break
                j += 1
            j = min(j + 1, n)
            out.append(c + re.sub(r"[^\n]", " ", text[i + 1:j - 1]) + (text[j - 1] if j - 1 > i else ""))
            i = j
        else:
            out.append(c); i += 1
    return "".join(out)


def _count_params(raw):
    depth, parts, cur = 0, [], ""
    for ch in raw:
        if ch in "<([{":
            depth += 1
        elif ch in ">)]}":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append(cur); cur = ""
        else:
            cur += ch
    parts.append(cur)
    return sum(1 for p in parts if p.strip())


def _body_end(code, start):
    """Index of the closing brace of a block body, or the end of an expression body."""
    depth, i, block = 0, start, code[start] == "{"
    while i < len(code):
        ch = code[i]
        if ch in "{([":
            depth += 1
        elif ch in "})]":
            depth -= 1
            if depth == 0 and block or depth < 0:
                return i if block else i - 1
        elif not block and depth == 0 and (ch in ";," or code.startswith("\n\n", i)):
            return i
        i += 1
    return len(code) - 1


def brace_functions(text):
    code = strip_code(text)
    starts = {}
    for rx in (FUNC_RE, ARROW_RE, EXPR_FUNC_RE, EXPR_ARROW_RE):
        for m in rx.finditer(code):
            name = m.group(1)
            if name in KEYWORDS:
                continue
            before = code[:m.start(1)].rstrip()
            prev_word = re.search(r"([A-Za-z_$][\w$]*)\s*$", before)
            if prev_word and prev_word.group(1) in DECL_WORDS:
                continue
            if before.endswith(".") and rx in (FUNC_RE, EXPR_FUNC_RE):
                continue  # a call like obj.method(x) {  -> not a declaration
            brace = m.end() - 1 if code[m.end() - 1] == "{" else m.end()
            starts.setdefault(brace, (name, m.start(1), m.group(2)))
    out = []
    for brace, (name, name_pos, params) in sorted(starts.items()):
        i = _body_end(code, brace)
        body = code[brace:i + 1]
        depth = max_depth = 0
        for ch in body:
            if ch == "{":
                depth += 1
                max_depth = max(max_depth, depth)
            elif ch == "}":
                depth -= 1
        if code[brace] != "{":
            max_depth += 1  # expression body: no outer brace to discount
        first = code.count("\n", 0, name_pos) + 1
        last = code.count("\n", 0, i) + 1
        out.append({
            "name": name, "line": first, "lines": last - first + 1,
            "nesting": max(0, max_depth - 1), "params": _count_params(params),
            "complexity": 1 + len(CONTROL_RE.findall(body)),
        })
    return out, None


# ------------------------------------------------------------------ SQL
SQL_HEAD = re.compile(
    r"\bCREATE\s+(?:OR\s+(?:ALTER|REPLACE)\s+)?(PROCEDURE|PROC|FUNCTION|TRIGGER)\s+([\w\[\]\".]+)", re.I)
SQL_TOKEN = re.compile(
    r"\bEND\s+(?:IF|LOOP|CASE|TRY|CATCH)\b|\bBEGIN\s+(?:TRY|CATCH)\b|"
    r"\bBEGIN\s+(?:TRAN|TRANSACTION|DISTRIBUTED)\b|\bBEGIN\b|\bEND\b|\bCASE\b|\bLOOP\b|\bIF\b", re.I)


def strip_sql(text):
    text = re.sub(r"/\*.*?\*/", lambda m: re.sub(r"[^\n]", " ", m.group()), text, flags=re.S)
    text = re.sub(r"--[^\n]*", lambda m: " " * len(m.group()), text)
    return re.sub(r"'(?:[^']|'')*'", lambda m: "'" + " " * (len(m.group()) - 2) + "'", text)


def sql_functions(text):
    code = strip_sql(text)
    heads = list(SQL_HEAD.finditer(code))
    out = []
    for k, m in enumerate(heads):
        end = heads[k + 1].start() if k + 1 < len(heads) else len(code)
        go = re.search(r"^\s*GO\s*$", code[m.end():end], re.M | re.I)
        if go:
            end = m.end() + go.start()
        body = code[m.start():end].rstrip()
        pg = re.search(r"\bEND\s+IF\b", body, re.I) is not None
        as_pos = re.search(r"\bAS\b|\$\$|\bLANGUAGE\b", body, re.I)
        header = body[:as_pos.start()] if as_pos else body
        if re.search(r"@\w+", header):
            params = len(set(p.lower() for p in re.findall(r"@\w+", header)))
        else:
            pm = re.search(PARAMS, header[m.end() - m.start():])
            params = _count_params(pm.group(1)) if pm else 0
        depth = max_depth = 0
        first_opener = None
        for t in SQL_TOKEN.finditer(body):
            tok = re.sub(r"\s+", " ", t.group().upper())
            if tok.startswith("BEGIN T") and tok != "BEGIN TRY" or tok.startswith("BEGIN D"):
                continue  # transactions do not nest blocks
            if tok == "IF" and not pg:
                continue  # T-SQL IF has no END; its BEGIN is counted instead
            if tok.startswith("END"):
                depth = max(0, depth - 1)
                continue
            if tok == "LOOP" and re.search(r"\bEND\s+$", body[:t.start()], re.I):
                continue
            first_opener = first_opener or tok
            depth += 1
            max_depth = max(max_depth, depth)
        if first_opener == "BEGIN":
            max_depth -= 1  # the procedure's own outer BEGIN ... END
        branches = len(re.findall(r"(?<!END )\bIF\b|\bELSIF\b|\bWHILE\b|\bWHEN\b|\bBEGIN\s+CATCH\b|\bEXCEPTION\b", body, re.I))
        branches += len(re.findall(r"\bFOR\s+\w+\s+IN\b", body, re.I))  # PL/pgSQL row loops
        cursors = len(re.findall(r"\bCURSOR\b", body, re.I)) + len(re.findall(r"\bFOR\s+\w+\s+IN\s+(?:SELECT|EXECUTE)\b", body, re.I))
        first = code.count("\n", 0, m.start()) + 1
        out.append({
            "name": m.group(2).strip('"[]'), "line": first,
            "lines": body.count("\n") + 1, "nesting": max(0, max_depth),
            "params": params, "complexity": 1 + branches, "cursors": cursors,
        })
    return out, None


# ------------------------------------------------------------ file + report
def _normalize(line, ext):
    s = line.strip()
    comment = ("#",) if ext == ".py" else ("//", "--", "/*", "*")
    if not s or s.startswith(comment) or re.fullmatch(r"[{}()\[\];,]+|(?i:begin|end|go)", s):
        return None
    return re.sub(r"\s+", " ", s)


def analyze_file(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    ext = path.suffix.lower()
    if ext == ".py":
        funcs, err = python_functions(text)
    elif ext == ".sql":
        funcs, err = sql_functions(text)
    else:
        funcs, err = brace_functions(text)
    lines = text.splitlines()
    norm = [(i + 1, _normalize(l, ext)) for i, l in enumerate(lines)]
    norm = [(i, s) for i, s in norm if s]
    for f in funcs:
        f["flags"] = [f"{k}>{v}" for k, v in LIMITS.items() if f[k] > v]
        if f.get("cursors"):
            f["flags"].append("cursor")
    return {
        "file": str(path), "lines": len(lines), "code_lines": len(norm),
        "functions": funcs, "error": err, "_norm": norm,
    }


def find_duplicates(files):
    seen = {}
    for fi, f in enumerate(files):
        norm = f["_norm"]
        for k in range(len(norm) - DUP_WINDOW + 1):
            key = hashlib.sha1("\n".join(s for _, s in norm[k:k + DUP_WINDOW]).encode()).hexdigest()
            seen.setdefault(key, []).append((fi, k))
    dup_starts = {}
    for occ in seen.values():
        if len(occ) > 1:
            for fi, k in occ:
                dup_starts.setdefault(fi, set()).add(k)
    for fi, f in enumerate(files):
        blocks, prev = [], None
        for k in sorted(dup_starts.get(fi, ())):
            line = f["_norm"][k][0]
            end = f["_norm"][k + DUP_WINDOW - 1][0]
            if prev is not None and k == prev + 1:
                blocks[-1][1] = end
            else:
                blocks.append([line, end])
            prev = k
        f["duplicate_blocks"] = [{"from": a, "to": b} for a, b in blocks]


def collect(paths):
    files = []
    for p in map(Path, paths):
        if p.is_dir():
            for f in sorted(p.rglob("*")):
                if f.is_file() and f.suffix.lower() in EXTS and not SKIP_DIRS & set(f.parts):
                    files.append(f)
        elif p.is_file():
            files.append(p)
        else:
            sys.exit(f"not found: {p}")
    return files


def analyze(paths):
    files = [analyze_file(f) for f in collect(paths)]
    find_duplicates(files)
    for f in files:
        del f["_norm"]
    return files


def summary(files):
    funcs = [fn for f in files for fn in f["functions"]]
    top = lambda k: max((fn[k] for fn in funcs), default=0)
    return {
        "files": len(files),
        "total_lines": sum(f["lines"] for f in files),
        "code_lines": sum(f["code_lines"] for f in files),
        "functions": len(funcs),
        "max_function_lines": top("lines"),
        "max_complexity": top("complexity"),
        "max_nesting": top("nesting"),
        "max_params": top("params"),
        "duplicate_blocks": sum(len(f["duplicate_blocks"]) for f in files),
        "sql_cursors": sum(fn.get("cursors", 0) for fn in funcs),
        "flagged_functions": sum(1 for fn in funcs if fn["flags"]),
    }


def print_report(files):
    for f in files:
        print(f"\n== {f['file']}  ({f['lines']} lines, {f['code_lines']} code, {len(f['functions'])} functions)")
        if f["error"]:
            print(f"   ! {f['error']}")
        if f["functions"]:
            print(f"   {'function':<34}{'line':>6}{'lines':>7}{'nest':>6}{'params':>8}{'cx':>5}  flags")
            for fn in f["functions"]:
                print(f"   {fn['name'][:33]:<34}{fn['line']:>6}{fn['lines']:>7}{fn['nesting']:>6}"
                      f"{fn['params']:>8}{fn['complexity']:>5}  {', '.join(fn['flags']) or '-'}")
        for d in f["duplicate_blocks"]:
            print(f"   duplicate block: lines {d['from']}-{d['to']}")
    print("\nSummary:", ", ".join(f"{k}={v}" for k, v in summary(files).items()))
    print(f"Thresholds: lines>{LIMITS['lines']} nesting>{LIMITS['nesting']} params>{LIMITS['params']} "
          f"complexity>{LIMITS['complexity']}; non-Python numbers are heuristic.")


def compare(before, after, as_json):
    b, a = summary(analyze([before])), summary(analyze([after]))
    rows = [(k, b[k], a[k], a[k] - b[k]) for k in b if k != "files"]
    if as_json:
        print(json.dumps({"before": b, "after": a, "delta": {k: d for k, _, _, d in rows}}, indent=2))
        return
    print(f"{'metric':<22}{'before':>8}{'after':>8}{'delta':>8}")
    for k, x, y, d in rows:
        pct = f"  ({d / x:+.0%})" if x else ""
        print(f"{k:<22}{x:>8}{y:>8}{d:>+8}{pct}")
    print("Lower is better for every row except functions (extracting helpers can raise it).")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("paths", nargs="*", help="files or folders to scan")
    ap.add_argument("--compare", nargs=2, metavar=("BEFORE", "AFTER"), help="print deltas between two files/folders")
    ap.add_argument("--json", action="store_true", help="JSON output")
    args = ap.parse_args()
    if args.compare:
        compare(*args.compare, args.json)
    elif args.paths:
        files = analyze(args.paths)
        if args.json:
            print(json.dumps({"files": files, "summary": summary(files)}, indent=2))
        else:
            print_report(files)
    else:
        ap.error("give paths to scan or --compare BEFORE AFTER")


if __name__ == "__main__":
    main()
