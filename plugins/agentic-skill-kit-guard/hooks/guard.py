#!/usr/bin/env python3
"""Hooks for the agentic-skill-kit-guard plugin. Python 3 stdlib only.

  post-edit   (PostToolUse on Write|Edit|MultiEdit): scan the edited file for HIGH/CRITICAL security
              issues (and SQL hazards for .sql). Findings go back to Claude (exit 2) so it fixes them.
  pre-commit  (PreToolUse on Bash): if the command is `git commit`, scan staged files for committed
              secrets and block the commit (exit 2) when one is found.

Never fails the session: any internal error exits 0 silently.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEC = ROOT / "hooks/scanners/sec_scan.py"
SQL = ROOT / "hooks/scanners/sql_lint.py"
SEC_EXT = {".cs", ".java", ".kt", ".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".yml", ".yaml", ".xml",
           ".config", ".properties", ".env", ".ini", ".toml", ".sql", ".tf", ".sh", ".ps1"}
SECRET_RULES = {"aws-access-key", "private-key", "hardcoded-password", "conn-string-password", "jwt-token",
                "high-entropy-secret"}
LINE = re.compile(r"^(\S.*?):(\d+):?\s+(CRITICAL|HIGH|ERROR)\s+\[?([\w-]+)\]?\s+(.*)$")


def run(script, files):
    out = subprocess.run([sys.executable, str(script), *files], capture_output=True, text=True, timeout=50).stdout
    return [m.groups() for m in (LINE.match(l.strip()) for l in out.splitlines()) if m]


def post_edit(data):
    path = (data.get("tool_input") or {}).get("file_path") or ""
    p = Path(path)
    if not p.is_file() or ROOT in p.resolve().parents:
        return 0
    hits = []
    if p.suffix.lower() in SEC_EXT or p.name.startswith(".env"):
        hits += run(SEC, [str(p)])
    if p.suffix.lower() == ".sql":
        hits += run(SQL, [str(p)])
    if not hits:
        return 0
    lines = [f"- {Path(f).name}:{no} {sev} {rule}: {msg[:150]}" for f, no, sev, rule, msg in hits[:10]]
    print("agentic-skill-kit-guard found HIGH-risk issues in the file just written. Fix them now "
          "(or explain why each is a false positive):\n" + "\n".join(lines), file=sys.stderr)
    return 2


def pre_commit(data):
    cmd = (data.get("tool_input") or {}).get("command") or ""
    if not re.search(r"\bgit\b[^;&|]*\bcommit\b", cmd):
        return 0
    staged = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
                            capture_output=True, text=True, timeout=20, cwd=data.get("cwd") or None).stdout.split()
    base = Path(data.get("cwd") or ".")
    files = [str(base / f) for f in staged if (base / f).is_file()]
    if not files:
        return 0
    secrets = [h for h in run(SEC, files) if h[3] in SECRET_RULES]
    if not secrets:
        return 0
    lines = [f"- {f}:{no} {rule}" for f, no, sev, rule, msg in secrets[:10]]
    print("Commit blocked by agentic-skill-kit-guard: staged files contain likely secrets (values masked):\n"
          + "\n".join(lines) + "\nMove them to env vars / a secret store and rotate them, or mark a reviewed "
          "false positive with a `nosec` comment, then commit again.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    try:
        payload = json.load(sys.stdin)
        mode = sys.argv[1] if len(sys.argv) > 1 else ""
        sys.exit(post_edit(payload) if mode == "post-edit" else pre_commit(payload) if mode == "pre-commit" else 0)
    except SystemExit:
        raise
    except Exception:
        sys.exit(0)
