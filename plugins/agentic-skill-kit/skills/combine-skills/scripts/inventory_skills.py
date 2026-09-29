#!/usr/bin/env python3
"""Inventory several skill folders and measure overlap between them.

Usage: python inventory_skills.py <skill-dir> <skill-dir> [...]
Prints per-skill summary, pairwise rule overlap and description-word overlap,
plus a hint for criterion #2 of the merge decision score.
"""
import itertools
import re
import sys
from pathlib import Path

STOP = set("""a an the and or of to for in on with by from is are be as at it this that
use when user asks ask if not no never always each every any all only into their your
you them its than then""".split())


def load(d):
    d = Path(d)
    text = (d / "SKILL.md").read_text(encoding="utf-8")
    for f in (d / "references").glob("*.md") if (d / "references").is_dir() else []:
        text += "\n" + f.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    front, body = (m.groups() if m else ("", text))
    name = (re.search(r"^name:\s*(.+)$", front, re.M) or [None, d.name])[1].strip()
    desc = (re.search(r"^description:\s*(.+)$", front, re.M) or [None, ""])[1].strip()
    bullets = [re.sub(r"^\s*(?:[-*]|\d+\.)\s+(\[.\]\s*)?", "", l).strip()
               for l in body.splitlines() if re.match(r"^\s*(?:[-*]|\d+\.)\s+", l)]
    sections = re.findall(r"^#{2,3}\s+(.+)$", body, re.M)
    return dict(name=name, desc=desc, bullets=bullets, sections=sections,
                lines=body.count("\n"), scripts=sorted(p.name for p in (d / "scripts").glob("*")) if (d / "scripts").is_dir() else [])


def words(s):
    return {w for w in re.findall(r"[a-z][a-z0-9-]+", s.lower()) if w not in STOP and len(w) > 2}


def sim(a, b):
    wa, wb = words(a), words(b)
    return len(wa & wb) / len(wa | wb) if wa and wb else 0.0


if len(sys.argv) < 3:
    sys.exit("Usage: inventory_skills.py <skill-dir> <skill-dir> [...]")
skills = [load(d) for d in sys.argv[1:]]

print("=== Skills ===")
for s in skills:
    print(f"\n[{s['name']}]  body+refs lines: {s['lines']}  rules/steps: {len(s['bullets'])}  scripts: {', '.join(s['scripts']) or '-'}")
    print(f"  description: {s['desc'][:200]}")
    print(f"  sections: {', '.join(s['sections'][:12])}")

print("\n=== Pairwise overlap ===")
overlaps = []
for a, b in itertools.combinations(skills, 2):
    matches = [(x, y, sim(x, y)) for x in a["bullets"] for y in b["bullets"]]
    similar = [m for m in matches if m[2] >= 0.5]
    matched_a = {m[0] for m in similar}
    pct = len(matched_a) / max(len(a["bullets"]), 1) * 100
    dsim = sim(a["desc"], b["desc"]) * 100
    overlaps.append(pct)
    print(f"\n{a['name']} <-> {b['name']}")
    print(f"  rule overlap: {pct:.0f}% of {a['name']}'s bullets have a near-duplicate in {b['name']}")
    print(f"  description word overlap: {dsim:.0f}%  " + ("(HIGH: skills may compete for triggers)" if dsim >= 35 else ""))
    for x, y, s in sorted(similar, key=lambda m: -m[2])[:5]:
        print(f"   ~{s:.2f}  '{x[:60]}'  |  '{y[:60]}'")

avg = sum(overlaps) / len(overlaps)
score = 2 if avg > 30 else 1 if avg >= 10 else 0
print(f"\nAverage rule overlap: {avg:.0f}%  -> merge criterion #2 (Shared rules) = {score}/2")
