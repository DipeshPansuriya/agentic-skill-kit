#!/usr/bin/env python3
"""Validate a skill folder. Exit code 1 if any ERROR.

Usage: python validate_skill.py <skill-dir>
"""
import re
import sys
from pathlib import Path

# Windows consoles default to cp1252; never crash on a non-ASCII message.
sys.stdout.reconfigure(errors="replace")

if len(sys.argv) != 2:
    sys.exit("Usage: validate_skill.py <skill-dir>")
root = Path(sys.argv[1])
errors, warns = [], []

skill = root / "SKILL.md"
if not skill.exists():
    print("ERROR: SKILL.md not found at folder root")
    sys.exit(1)
text = skill.read_text(encoding="utf-8")

m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
if not m:
    errors.append("Missing or malformed frontmatter (--- ... ---)")
    front, body = "", text
else:
    front, body = m.groups()

def field(key):
    fm = re.search(rf"^{key}:\s*(.+)$", front, re.M)
    return fm.group(1).strip().strip('"\'') if fm else None

name, desc = field("name"), field("description")
if not name:
    errors.append("frontmatter: 'name' missing")
else:
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name):
        errors.append(f"name '{name}' is not kebab-case")
    if len(name) > 64:
        errors.append("name > 64 chars")
    if re.search(r"claude|anthropic", name):
        errors.append("name contains 'claude' or 'anthropic'")
    if name != root.resolve().name:
        warns.append(f"name '{name}' differs from folder name '{root.resolve().name}'")

if not desc:
    errors.append("frontmatter: 'description' missing")
else:
    if len(desc) > 1024:
        errors.append(f"description is {len(desc)} chars (max 1024)")
    elif len(desc) > 250:
        warns.append(f"description is {len(desc)} chars (aim ≤ 250)")
    if "<" in desc or ">" in desc:
        errors.append("description contains angle brackets / placeholders")
    if not re.search(r"\buse (it )?when\b", desc, re.I):
        warns.append("description has no 'Use when…' clause")

lines = body.count("\n")
if lines > 500:
    errors.append(f"body is {lines} lines (max 500); move detail to references/")
elif lines > 300:
    warns.append(f"body is {lines} lines; consider moving detail to references/")

prose = re.sub(r"```.*?```", "", body, flags=re.S)
placeholders = re.findall(r"<[a-zA-Z][^>\n]{0,60}>", prose)
if placeholders:
    warns.append(f"{len(placeholders)} unfilled placeholder(s), e.g. {placeholders[0]}")

# Only skill-relative paths: skip a match inside a URL or a longer path (e.g. the user's `.specify/scripts/...`).
for ref in sorted(set(re.findall(r"(?<![\w./:-])((?:references|templates|scripts|evals)/[\w./-]+)", body))):
    ref = ref.rstrip(".,)")
    if not (root / ref).exists():
        errors.append(f"referenced file missing: {ref}")

for sub in ["references", "templates", "scripts", "evals"]:
    d = root / sub
    if d.is_dir():
        for f in d.rglob("*"):
            if f.is_file() and f"{sub}/{f.relative_to(d).as_posix()}" not in body:
                warns.append(f"{sub}/{f.relative_to(d).as_posix()} is never mentioned in SKILL.md")

if not re.search(r"self-check", body, re.I):
    warns.append("no self-check section")
if not (root / "evals").is_dir():
    warns.append("no evals/ folder (fine for L1/L2)")

print(f"Skill: {name or '?'}  |  body lines: {lines}  |  description chars: {len(desc or '')}")
for e in errors:
    print("ERROR:", e)
for w in warns:
    print("WARN: ", w)
print("RESULT:", "FAIL" if errors else "PASS", f"({len(errors)} errors, {len(warns)} warnings)")
sys.exit(1 if errors else 0)
