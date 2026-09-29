#!/usr/bin/env python3
"""Build an empty results CSV from an evals/test-cases.md table.

Reads markdown table rows: | # | Type | Request | Should trigger? | Expected |
Type containing 'near-miss' or Should trigger starting with 'No' -> should_trigger=0.

Usage:
  python build_results_sheet.py test-cases.md --versions A B [--repeat 3 --repeat-cases 1,2,3] [-o results.csv]
"""
import argparse
import csv
import re
import sys

COLS = ["case_id", "type", "should_trigger", "version", "run", "triggered", "routed_ok",
        "q_format", "q_facts", "q_no_invent", "q_rules", "q_usable", "critical",
        "structure", "tokens", "seconds", "notes"]

p = argparse.ArgumentParser()
p.add_argument("testcases")
p.add_argument("--versions", nargs="+", default=["A", "B"])
p.add_argument("--repeat", type=int, default=3)
p.add_argument("--repeat-cases", default="")
p.add_argument("-o", "--out", default="-")
a = p.parse_args()

rows = []
for line in open(a.testcases, encoding="utf-8"):
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    if len(cells) < 4 or not re.fullmatch(r"\d+", cells[0]):
        continue
    cid, typ, _req, trig = cells[:4]
    t = typ.lower()
    should = 0 if ("near-miss" in t or re.match(r"\**no", trig.lower())) else 1
    ctype = ("near-miss" if "near-miss" in t else "edge" if "edge" in t
             else "multi" if ("multi" in t or "week-over-week" in t) else "single")
    rows.append((cid, ctype, should))

if not rows:
    sys.exit("No test-case rows found (expected a markdown table starting with a numeric # column)")

rep = {c.strip() for c in a.repeat_cases.split(",") if c.strip()}
out = sys.stdout if a.out == "-" else open(a.out, "w", newline="", encoding="utf-8")
w = csv.writer(out)
w.writerow(COLS)
n = 0
for cid, ctype, should in rows:
    for v in a.versions:
        for r in range(1, (a.repeat if cid in rep else 1) + 1):
            w.writerow([cid, ctype, should, v, r] + [""] * (len(COLS) - 5))
            n += 1
if out is not sys.stdout:
    out.close()
    print(f"Wrote {n} rows for {len(rows)} cases x {len(a.versions)} versions -> {a.out}")
