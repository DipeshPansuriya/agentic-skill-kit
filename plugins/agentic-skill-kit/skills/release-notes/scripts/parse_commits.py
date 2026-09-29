#!/usr/bin/env python3
"""Group Conventional Commits into release-note categories (markdown).

Input: `git log --oneline` style lines ("<hash> <type>(<scope>)!: <subject>"),
hash optional. Body/footer lines (e.g. from `git log --format='%h %s%n%b'`) that
follow a commit are attached to it; a "BREAKING CHANGE:" / "BREAKING-CHANGE:"
footer, or "!" before the colon, marks the commit breaking.

Mapping:
  feat -> New | fix -> Fixed | perf -> Improved | refactor -> Internal
  docs -> Docs | chore/build/ci/test/style -> Maintenance
  breaking (any type) -> Breaking / Action required (also kept in its own category)
  non-conventional -> Unclassified (review manually); merge commits skipped

Usage:
  git log --oneline v1.4.0..v1.5.0 | python parse_commits.py -
  python parse_commits.py commits.txt [--client]
  --client  hide hashes, ticket IDs and internal-only categories (Internal, Docs, Maintenance)
"""
import argparse
import re
import sys

HEADER = re.compile(
    r"^(?:(?P<hash>[0-9a-f]{7,40})\s+)?(?P<type>[a-z]+)(?:\((?P<scope>[^)]+)\))?(?P<bang>!)?:\s*(?P<subject>.+)$",
    re.I,
)
HASH_ONLY = re.compile(r"^(?P<hash>[0-9a-f]{7,40})\s+(?P<subject>.+)$", re.I)
BREAKING = re.compile(r"^\s*BREAKING[ -]CHANGE:\s*(?P<text>.+)$")
TICKET = re.compile(r"\b[A-Z][A-Z0-9]+-\d+\b|#\d+\b")

CATEGORY = {"feat": "New", "fix": "Fixed", "perf": "Improved", "refactor": "Internal",
            "docs": "Docs", "chore": "Maintenance", "build": "Maintenance", "ci": "Maintenance",
            "test": "Maintenance", "style": "Maintenance", "revert": "Fixed"}
ORDER = ["Breaking / Action required", "New", "Improved", "Fixed", "Internal", "Docs",
         "Maintenance", "Unclassified (review manually)"]
INTERNAL_ONLY = {"Internal", "Docs", "Maintenance", "Unclassified (review manually)"}


def parse(lines):
    commits = []
    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            continue
        b = BREAKING.match(line)
        if b and commits:
            commits[-1]["breaking"] = True
            commits[-1]["breaking_note"] = b["text"].strip()
            continue
        m = HEADER.match(line.strip())
        if m and m["type"].lower() in CATEGORY:
            commits.append({"hash": m["hash"] or "", "type": m["type"].lower(), "scope": m["scope"] or "",
                            "subject": m["subject"].strip(), "breaking": bool(m["bang"]), "breaking_note": ""})
            continue
        h = HASH_ONLY.match(line.strip())
        if h:
            subj = h["subject"].strip()
            if subj.lower().startswith(("merge pull request", "merge branch", "merge remote")):
                continue
            commits.append({"hash": h["hash"], "type": "", "scope": "", "subject": subj,
                            "breaking": False, "breaking_note": ""})
        # anything else is a body line: ignored unless it is a BREAKING footer (handled above)
    return commits


def render(commits, client):
    groups = {k: [] for k in ORDER}
    for c in commits:
        cat = CATEGORY.get(c["type"], "Unclassified (review manually)")
        groups[cat].append(c)
        if c["breaking"]:
            groups["Breaking / Action required"].append(c)
    out = []
    for cat in ORDER:
        items = groups[cat]
        if not items or (client and cat in INTERNAL_ONLY):
            continue
        out.append(f"### {cat}")
        for c in items:
            text = c["subject"]
            if cat == "Breaking / Action required" and c["breaking_note"]:
                text += f": {c['breaking_note']}"
            if client:
                text = re.sub(r"\s*\(?(" + TICKET.pattern + r")\)?", "", text).strip()
                out.append(f"- {text}")
            else:
                scope = f"**{c['scope']}**: " if c["scope"] else ""
                ref = f" (`{c['hash']}`)" if c["hash"] else ""
                out.append(f"- {scope}{text}{ref}")
        out.append("")
    total = len(commits)
    unc = len(groups["Unclassified (review manually)"])
    out.append(f"_Parsed {total} commit(s); {len(groups['Breaking / Action required'])} breaking; {unc} unclassified._")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", help="input file, or - for stdin")
    ap.add_argument("--client", action="store_true", help="client-facing: no hashes/ticket IDs/internal categories")
    a = ap.parse_args()
    src = sys.stdin if a.file == "-" else open(a.file, encoding="utf-8")
    commits = parse(src)
    if not commits:
        sys.exit("No commits found. Expected lines like 'a1b2c3d feat(scope): subject'.")
    print(render(commits, a.client))


if __name__ == "__main__":
    main()
