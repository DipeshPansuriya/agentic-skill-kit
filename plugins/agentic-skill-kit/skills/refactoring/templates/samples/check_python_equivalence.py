#!/usr/bin/env python3
"""Golden-master check: python_before.calc_charge vs python_after.calc_charge.

Runs both on a fixed grid plus seeded random inputs (edge cases: weight-break
boundaries, half-kg rounding, None/0/negative/NaN, 1/0/"Y" flags, unknown commodity)
and compares the result or the exception type + message.
Usage: python3 check_python_equivalence.py     (exit 1 on any mismatch)
"""
import itertools
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import python_after as after  # noqa: E402
import python_before as before  # noqa: E402


def outcome(fn, *args):
    try:
        return ("ok", fn(*args))
    except Exception as e:  # compare failures too
        return ("err", type(e).__name__, str(e))


weights = [None, 0, -1, float("nan"), 0.2, 10, 10.3, 10.5, 10.7, 44.9, 45, 45.0, 99.5, 100, 299.99, 300, 499.6, 500, 1234.4]
dims = [(10, 10, 10), (60, 50, 40), (120, 100, 80)]
cases = list(itertools.product(weights, dims, [None, 0, 1, 3], ["GEN", "PER", "XXX"],
                               [True, False, 1, 0, "Y"], ["KEY", "STD"], [True, False]))
rng = random.Random(42)
for _ in range(20000):
    cases.append((round(rng.uniform(0.1, 2000), rng.choice([0, 1, 2, 3])),
                  tuple(rng.randint(1, 150) for _ in range(3)), rng.randint(1, 20),
                  rng.choice(["GEN", "PER"]), rng.choice([True, False]),
                  rng.choice(["KEY", "STD"]), rng.choice([True, False])))

mismatches = 0
for kg, (l, w, h), pcs, com, dg, cust, exp in cases:
    args = ("AWB-000-00000000", kg, l, w, h, pcs, com, dg, cust, exp)
    b, a = outcome(before.calc_charge, *args), outcome(after.calc_charge, *args)
    if b != a:
        mismatches += 1
        if mismatches <= 5:
            print("MISMATCH", args, b, a)

items = [{"awb": "x", "kg": 12.3, "l": 50, "w": 40, "h": 30, "pcs": 2, "commodity": "PER",
          "dg": True, "cust": "KEY", "express": False}] * 3
list_ok = before.calc_charge_list(items) == after.calc_charge_list(items)
print(f"cases={len(cases)} mismatches={mismatches} list_equal={list_ok}")
sys.exit(1 if mismatches or not list_ok else 0)
