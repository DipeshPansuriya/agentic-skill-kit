#!/usr/bin/env python3
"""Score a filled results CSV and print scorecard + verdict.

Usage: python score_benchmark.py results.csv [--baseline A] [--candidate B] [--md report.md]
Columns: see templates/results-template.csv
"""
import argparse
import csv
from collections import defaultdict
from statistics import mean

Q = ["q_format", "q_facts", "q_no_invent", "q_rules", "q_usable"]
T = dict(trigger_acc=90, recall=95, false_trigger=10, quality=4.0, consistency=100, cost_ratio=1.3)


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def pct(n, d):
    return 100 * n / d if d else None


def stats(rows):
    s = {}
    judged = [r for r in rows if num(r["triggered"]) is not None]
    correct = sum(1 for r in judged if int(num(r["triggered"])) == int(num(r["should_trigger"])))
    pos = [r for r in judged if num(r["should_trigger"]) == 1]
    neg = [r for r in judged if num(r["should_trigger"]) == 0]
    trig = [r for r in judged if num(r["triggered"]) == 1]
    s["trigger_acc"] = pct(correct, len(judged))
    s["recall"] = pct(sum(num(r["triggered"]) == 1 for r in pos), len(pos))
    s["precision"] = pct(sum(num(r["should_trigger"]) == 1 for r in trig), len(trig))
    s["false_trigger"] = pct(sum(num(r["triggered"]) == 1 for r in neg), len(neg))
    routed = [num(r["routed_ok"]) for r in rows if num(r["routed_ok"]) is not None]
    s["routing"] = pct(sum(routed), len(routed))
    qs = []
    for r in pos:
        vals = [num(r[c]) for c in Q]
        if all(v is not None for v in vals):
            qs.append(sum(vals))
    s["quality"] = mean(qs) if qs else None
    s["critical"] = sum(1 for r in rows if num(r.get("critical")) == 1)
    s["critical_cases"] = sorted({r["case_id"] for r in rows if num(r.get("critical")) == 1}, key=lambda x: int(x) if x.isdigit() else 0)
    groups = defaultdict(set)
    counts = defaultdict(int)
    for r in rows:
        counts[r["case_id"]] += 1
        if r.get("structure"):
            groups[r["case_id"]].add(r["structure"].strip().lower())
    reps = [c for c, n in counts.items() if n > 1 and groups[c]]
    s["consistency"] = pct(sum(len(groups[c]) == 1 for c in reps), len(reps))
    tk = [num(r["tokens"]) for r in rows if num(r["tokens"]) is not None]
    sc = [num(r["seconds"]) for r in rows if num(r["seconds"]) is not None]
    s["tokens"] = mean(tk) if tk else None
    s["seconds"] = mean(sc) if sc else None
    s["fails"] = sorted({r["case_id"] for r in judged if int(num(r["triggered"])) != int(num(r["should_trigger"]))}, key=lambda x: int(x) if x.isdigit() else 0)
    low = set()
    for r in pos:
        vals = [num(r[c]) for c in Q]
        if all(v is not None for v in vals) and sum(vals) < 4:
            low.add(r["case_id"])
    s["low_quality"] = sorted(low, key=lambda x: int(x) if x.isdigit() else 0)
    return s


def fmt(v, kind="pct"):
    if v is None:
        return "–"
    return f"{v:.0f}%" if kind == "pct" else f"{v:.2f}" if kind == "q" else f"{v:.0f}"


def verdict(a, b):
    reasons = []
    if b["critical"] > a["critical"]:
        return "KEEP BASELINE", [f"candidate has {b['critical']} critical failure(s) (cases {', '.join(b['critical_cases'])})"]
    misses = []
    if b["trigger_acc"] is not None and b["trigger_acc"] < T["trigger_acc"]:
        misses.append(f"trigger accuracy {fmt(b['trigger_acc'])} < {T['trigger_acc']}%")
    if b["false_trigger"] is not None and b["false_trigger"] > T["false_trigger"]:
        misses.append(f"false-trigger rate {fmt(b['false_trigger'])} > {T['false_trigger']}%")
    if b["quality"] is not None and b["quality"] < T["quality"]:
        misses.append(f"quality {fmt(b['quality'], 'q')} < {T['quality']}")
    if b["consistency"] is not None and b["consistency"] < T["consistency"]:
        misses.append(f"consistency {fmt(b['consistency'])} < 100%")
    if b["critical"]:
        misses.append(f"{b['critical']} critical failure(s)")
    if misses:
        return "FIX & RETEST", misses
    if a["quality"] is not None and b["quality"] is not None and b["quality"] <= a["quality"] - 0.2:
        return "KEEP BASELINE", [f"quality dropped {fmt(a['quality'], 'q')} -> {fmt(b['quality'], 'q')}"]
    if a["trigger_acc"] is not None and b["trigger_acc"] is not None and b["trigger_acc"] <= a["trigger_acc"] - 5:
        return "KEEP BASELINE", [f"trigger accuracy dropped {fmt(a['trigger_acc'])} -> {fmt(b['trigger_acc'])}"]
    if a["tokens"] and b["tokens"] and b["tokens"] > a["tokens"] * T["cost_ratio"]:
        gain = (b["quality"] or 0) - (a["quality"] or 0)
        if gain < 0.2:
            return "FIX & RETEST", [f"cost {b['tokens'] / a['tokens']:.2f}x baseline with quality gain {gain:+.2f}"]
    if a["quality"] is not None and b["quality"] is not None:
        d = b["quality"] - a["quality"]
        reasons.append(f"quality {fmt(a['quality'], 'q')} -> {fmt(b['quality'], 'q')} ({d:+.2f}{', tie' if abs(d) < 0.2 else ''})")
    if a["trigger_acc"] is not None and b["trigger_acc"] is not None:
        reasons.append(f"trigger accuracy {fmt(a['trigger_acc'])} -> {fmt(b['trigger_acc'])}")
    return "SHIP", reasons + ["all targets met"]


p = argparse.ArgumentParser()
p.add_argument("csv")
p.add_argument("--baseline", default="A")
p.add_argument("--candidate", default="B")
p.add_argument("--md")
args = p.parse_args()

rows = list(csv.DictReader(open(args.csv, encoding="utf-8")))
by_v = defaultdict(list)
for r in rows:
    by_v[r["version"]].append(r)
A, B = stats(by_v[args.baseline]), stats(by_v[args.candidate])

lines = [f"# Benchmark: {args.baseline} (baseline) vs {args.candidate} (candidate)",
         f"Cases: {len({r['case_id'] for r in rows})} · Runs: {len(rows)}", "",
         "| Metric | A | B | Target |", "|---|---|---|---|"]
for label, key, kind, tgt in [
    ("Trigger accuracy", "trigger_acc", "pct", "≥ 90%"), ("Recall", "recall", "pct", "≥ 95%"),
    ("Precision", "precision", "pct", "≥ 90%"), ("False-trigger rate", "false_trigger", "pct", "≤ 10%"),
    ("Routing accuracy", "routing", "pct", "100%"), ("Avg quality (0–5)", "quality", "q", "≥ 4.0"),
    ("Critical failures", "critical", "n", "0"), ("Consistency", "consistency", "pct", "100%"),
    ("Avg tokens", "tokens", "n", "≤ A × 1.3"), ("Avg seconds", "seconds", "n", "")]:
    lines.append(f"| {label} | {fmt(A[key], kind)} | {fmt(B[key], kind)} | {tgt} |")

lines += ["", "## By type (avg quality / trigger accuracy)", "| Type | A | B |", "|---|---|---|"]
for t in ["single", "multi", "edge", "near-miss"]:
    sa = stats([r for r in by_v[args.baseline] if r["type"] == t])
    sb = stats([r for r in by_v[args.candidate] if r["type"] == t])
    lines.append(f"| {t} | {fmt(sa['quality'], 'q')} / {fmt(sa['trigger_acc'])} | {fmt(sb['quality'], 'q')} / {fmt(sb['trigger_acc'])} |")

v, why = verdict(A, B)
lines += ["", f"## Verdict: {v}"] + [f"- {x}" for x in why]
lines += ["", "## Failing cases (candidate)",
          f"- Wrong trigger decision: {', '.join(B['fails']) or 'none'}",
          f"- Quality < 4: {', '.join(B['low_quality']) or 'none'}",
          f"- Critical: {', '.join(B['critical_cases']) or 'none'}"]

out = "\n".join(lines)
print(out)
if args.md:
    open(args.md, "w", encoding="utf-8").write(out + "\n")
