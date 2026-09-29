#!/usr/bin/env python3
"""Create a skill folder skeleton.

Usage: python scaffold_skill.py <skill-name> [--level 1|2|3] [--out DIR]
"""
import argparse
import re
import sys
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument("name")
p.add_argument("--level", type=int, choices=[1, 2, 3], default=1)
p.add_argument("--out", default=".")
a = p.parse_args()

if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", a.name) or len(a.name) > 64:
    sys.exit("ERROR: name must be kebab-case, ≤ 64 chars")
if re.search(r"claude|anthropic", a.name):
    sys.exit("ERROR: name must not contain 'claude' or 'anthropic'")

root = Path(a.out) / a.name
if root.exists():
    sys.exit(f"ERROR: {root} already exists")
root.mkdir(parents=True)

title = a.name.replace("-", " ").title()
refs = ""
if a.level >= 2:
    (root / "references").mkdir()
    (root / "templates").mkdir()
    (root / "references" / "details.md").write_text("# Details\n\n<Long rules, variants, lookup tables>\n")
    (root / "templates" / "output-template.md").write_text("# <Output title>\n\n## Section 1\n\n## Section 2\n")
    refs = "\n## References\n- Detailed rules: `references/details.md`\n- Output skeleton: `templates/output-template.md`\n"
if a.level >= 3:
    (root / "scripts").mkdir()
    (root / "evals").mkdir()
    (root / "scripts" / "helper.py").write_text('#!/usr/bin/env python3\n"""<What this script does exactly>."""\n')
    (root / "evals" / "test-cases.md").write_text(
        "# Test Cases\n\n| # | Type | Request | Should trigger? | Expected |\n|---|---|---|---|---|\n| 1 | Single | | Yes | |\n| 2 | Near-miss | | No | |\n")
    refs += "- Exact operations: `scripts/helper.py`\n- Tests: `evals/test-cases.md`\n"

(root / "SKILL.md").write_text(f"""---
name: {a.name}
description: <Verb + what it produces>. Use when the user <trigger phrase 1>, <trigger phrase 2>, or <trigger phrase 3>.
---

# {title}

## Inputs
- <input>

## Steps
1. Read all input before writing.
2. <step>
3. Run the self-check.

## Format
<exact structure>

## Rules
- Never invent data. Use "TBD" and list under Needs input.
{refs}
## Self-check
- [ ] Format followed
- [ ] Nothing invented
""")

print(f"Created L{a.level} skill at {root}")
for f in sorted(root.rglob("*")):
    print("  ", f.relative_to(root.parent))
