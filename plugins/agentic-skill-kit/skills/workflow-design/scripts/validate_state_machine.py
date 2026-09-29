#!/usr/bin/env python3
"""Validate a state machine written as a markdown transition table.

Reads every markdown table whose header has From, Event and To columns
(case-insensitive; extra columns such as Guard, Action, SLA are allowed).

Checks
  - unreachable states      (not reachable from the initial state)
  - dead-end states         (no outgoing transition and not declared terminal)
  - duplicate transitions   (same From + Event + Guard + To listed twice)
  - non-deterministic       (same From + Event + Guard leads to different To)
  - terminal with exits     (declared terminal but has outgoing transitions: WARN)

Conventions in the markdown (all optional)
  Initial: Booked                     line declaring the initial state
  Terminal: Delivered, Cancelled      line declaring terminal states
  From cell "A, B"                    same transition from several states
  From cell "*"                       from every non-terminal state (explicit
                                      rows for the same From + Event win)
  Backticks and **bold** around names are ignored.

Defaults: initial = From of the first row; terminal = none declared.

Usage
  python3 validate_state_machine.py <file.md> [--initial STATE] [--terminal S1,S2]
Exit code 0 = no errors, 1 = errors found, 2 = bad input.
"""
import re
import sys
from collections import defaultdict, deque


def clean(cell):
    cell = cell.strip()
    if cell == "*":
        return cell
    return re.sub(r"`|\*\*|__", "", cell).strip()


def split_row(line):
    return [clean(c) for c in line.strip().strip("|").split("|")]


def parse(text):
    initial, terminal, rows = None, set(), []
    m = re.search(r"^\s*[-*]?\s*\**initial\**\s*(?:state)?\s*:\s*(.+)$", text, re.I | re.M)
    if m:
        initial = clean(m.group(1)).split(",")[0].strip()
    m = re.search(r"^\s*[-*]?\s*\**terminal\**\s*(?:states?)?\s*:\s*(.+)$", text, re.I | re.M)
    if m:
        terminal = {clean(s) for s in m.group(1).split(",") if clean(s)}

    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|?[\s:|-]+\|?\s*$", lines[i + 1]) and "-" in lines[i + 1]:
            header = [h.lower() for h in split_row(line)]
            if {"from", "event", "to"} <= set(header):
                fi, ei, ti = header.index("from"), header.index("event"), header.index("to")
                gi = header.index("guard") if "guard" in header else None
                i += 2
                while i < len(lines) and lines[i].strip().startswith("|"):
                    cells = split_row(lines[i])
                    if len(cells) > max(fi, ei, ti):
                        guard = cells[gi] if gi is not None and gi < len(cells) else ""
                        guard = "" if guard in ("-", "—", "") else guard
                        rows.append((cells[fi], cells[ei], cells[ti], guard, i + 1))
                    i += 1
                continue
        i += 1
    return initial, terminal, rows


def main(argv):
    args = argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 2
    path, initial_arg, terminal_arg = args[0], None, None
    if "--initial" in args:
        initial_arg = args[args.index("--initial") + 1]
    if "--terminal" in args:
        terminal_arg = {s.strip() for s in args[args.index("--terminal") + 1].split(",") if s.strip()}

    try:
        text = open(path, encoding="utf-8").read()
    except OSError as e:
        print(f"ERROR: cannot read {path}: {e}")
        return 2
    initial, terminal, raw = parse(text)
    if not raw:
        print("ERROR: no markdown table with From | Event | To columns found")
        return 2
    initial = initial_arg or initial
    terminal = terminal_arg if terminal_arg is not None else terminal

    states = set(terminal)
    for f, _, t, _, _ in raw:
        states.update(s.strip() for s in f.split(",") if s.strip() and s.strip() != "*")
        states.add(t)
    if initial is None:
        initial = [s.strip() for s in raw[0][0].split(",")][0]
    if initial == "*" or initial not in states:
        print(f"ERROR: initial state '{initial}' is not a state in the table")
        return 2

    # Expand multi-source and wildcard rows
    explicit = {(s.strip(), e) for f, e, _, _, _ in raw if f.strip() != "*" for s in f.split(",")}
    rows = []
    for f, e, t, g, ln in raw:
        wild = f.strip() == "*"
        sources = sorted(states - terminal) if wild else [s.strip() for s in f.split(",") if s.strip()]
        for s in sources:
            if wild and (s == t or (s, e) in explicit):
                continue  # wildcard adds no self-loop and never overrides an explicit row
            rows.append((s, e, t, g, ln))

    errors, warns = [], []
    seen, targets = {}, defaultdict(set)
    for s, e, t, g, ln in rows:
        key = (s, e, g)
        if (s, e, g, t) in seen:
            errors.append(f"duplicate transition: {s} --{e}{'[' + g + ']' if g else ''}--> {t} (lines {seen[(s, e, g, t)]} and {ln})")
        else:
            seen[(s, e, g, t)] = ln
        targets[key].add(t)
    for (s, e, g), ts in sorted(targets.items()):
        if len(ts) > 1:
            errors.append(f"non-deterministic: {s} --{e}{'[' + g + ']' if g else ''}--> {', '.join(sorted(ts))} (add distinct guards or events)")

    out = defaultdict(set)
    for s, _, t, _, _ in rows:
        out[s].add(t)
    reached, queue = {initial}, deque([initial])
    while queue:
        for nxt in out[queue.popleft()]:
            if nxt not in reached:
                reached.add(nxt)
                queue.append(nxt)
    for s in sorted(states - reached):
        errors.append(f"unreachable state: {s} (no path from initial '{initial}')")
    for s in sorted(states - terminal):
        if not out[s]:
            errors.append(f"dead-end state: {s} (no outgoing transition and not declared terminal)")
    for s in sorted(terminal):
        if out[s]:
            warns.append(f"terminal state has outgoing transitions: {s} -> {', '.join(sorted(out[s]))}")
    if not terminal:
        warns.append("no terminal states declared (add a 'Terminal: A, B' line or --terminal)")

    print(f"States: {len(states)} | Transitions: {len(rows)} | Initial: {initial} | Terminal: {', '.join(sorted(terminal)) or 'none'}")
    for e in errors:
        print("ERROR:", e)
    for w in warns:
        print("WARN: ", w)
    print("RESULT:", "FAIL" if errors else "PASS", f"({len(errors)} errors, {len(warns)} warnings)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
