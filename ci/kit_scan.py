#!/usr/bin/env python3
"""Run the skill-kit scanners as one CI quality gate. Python 3 stdlib only.

Scanners (from the kit's skills/ folder):
  security     security-review-fix/scripts/sec_scan.py    code, config, .env, IaC
  performance  code-performance/scripts/perf_smells.py    .cs .java .py .ts .tsx .js
  sql          sql-performance-tuning/scripts/sql_lint.py .sql
  playwright   playwright-testing/scripts/flaky_scan.py   *.spec.* / *.test.* / tests/ e2e/ files

Usage:
  python kit_scan.py [PATH ...]                     scan paths (default: .)
  python kit_scan.py --changed origin/main          scan only files changed vs a git ref (PR mode)
Options:
  --kit DIR          folder containing skills/ (default: ../plugins/agentic-skill-kit)
  --fail-on LEVEL    CRITICAL | HIGH | MED | LOW | NONE   (default: HIGH)
  --only a,b         run a subset: security,performance,sql,playwright
  --md FILE          write a markdown summary (use $GITHUB_STEP_SUMMARY in GitHub Actions)
  --sarif FILE       write SARIF 2.1.0 (GitHub code scanning / Azure DevOps SARIF viewer)
  --baseline FILE    JSON of accepted findings to ignore; --write-baseline FILE creates it
Exit code: 1 if any finding at or above --fail-on (after baseline), 2 on usage error, else 0.
Findings are heuristic leads: confirm each one; suppress a reviewed line with `nosec` (security).
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

SEV_ORDER = ["LOW", "MED", "HIGH", "CRITICAL"]
MAP = {"ERROR": "HIGH", "WARN": "MED", "WARNING": "MED", "INFO": "LOW", "MEDIUM": "MED"}
LINE = re.compile(r"^(?P<file>.+?):(?P<line>\d+):?\s+(?P<sev>CRITICAL|HIGH|MED|MEDIUM|LOW|ERROR|WARN|WARNING|INFO)\s+"
                  r"\[?(?P<rule>[\w-]+)\]?\s+(?P<msg>.*)$")
CODE_EXT = {".cs", ".java", ".py", ".ts", ".tsx", ".js", ".jsx", ".mjs"}
SEC_EXT = CODE_EXT | {".kt", ".json", ".yml", ".yaml", ".xml", ".config", ".properties", ".env", ".ini", ".toml",
                      ".sql", ".tf", ".sh", ".ps1", ".cfg", ".html"}
SKIP = {"node_modules", ".git", "bin", "obj", "target", "dist", "build", ".venv", "venv", "__pycache__"}
TEST_FILE = re.compile(r"(\.|_)(spec|test)\.(ts|tsx|js|mjs|py)$|^test_.*\.py$", re.I)

SCANNERS = {
    "security": ("security-review-fix/scripts/sec_scan.py",
                 lambda p: p.suffix.lower() in SEC_EXT or p.name.startswith(".env") or p.name == "Dockerfile"),
    "performance": ("code-performance/scripts/perf_smells.py", lambda p: p.suffix.lower() in CODE_EXT),
    "sql": ("sql-performance-tuning/scripts/sql_lint.py", lambda p: p.suffix.lower() == ".sql"),
    "playwright": ("playwright-testing/scripts/flaky_scan.py",
                   lambda p: bool(TEST_FILE.search(p.name)) or bool({"e2e", "tests", "playwright"} & {x.lower() for x in p.parts})
                   and p.suffix.lower() in {".ts", ".tsx", ".js", ".mjs", ".py"}),
}


def git_changed(ref):
    try:
        out = subprocess.run(["git", "diff", "--name-only", "--diff-filter=ACMR", f"{ref}...HEAD"],
                             capture_output=True, text=True, check=True).stdout
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        sys.exit(f"kit_scan: cannot diff against {ref}: {getattr(e, 'stderr', e)}")
    return [Path(f) for f in out.splitlines() if f and Path(f).is_file()]


def collect(paths):
    files = []
    for p in map(Path, paths):
        if p.is_dir():
            files += [f for f in p.rglob("*") if f.is_file() and not SKIP & set(f.parts)]
        elif p.is_file():
            files.append(p)
    return files


def run(kit, name, files):
    script, want = SCANNERS[name]
    targets = [str(f) for f in files if want(f)]
    if not targets:
        return [], 0
    found = []
    for i in range(0, len(targets), 200):  # keep command lines short on Windows agents
        proc = subprocess.run([sys.executable, str(kit / "skills" / script), *targets[i:i + 200]],
                              capture_output=True, text=True)
        for raw in proc.stdout.splitlines():
            m = LINE.match(raw.strip())
            if m:
                sev = MAP.get(m["sev"], m["sev"])
                found.append({"scanner": name, "file": m["file"], "line": int(m["line"]), "severity": sev,
                              "rule": m["rule"], "message": re.sub(r"\s+", " ", m["msg"]).strip()})
        if proc.returncode not in (0, 1):
            print(f"kit_scan: {name} scanner error:\n{proc.stderr.strip()}", file=sys.stderr)
    return found, len(targets)


def fingerprint(f):
    return hashlib.sha1(f"{f['scanner']}|{f['file']}|{f['rule']}|{f['message']}".encode()).hexdigest()[:16]


def to_sarif(findings):
    level = {"CRITICAL": "error", "HIGH": "error", "MED": "warning", "LOW": "note"}
    runs = []
    for scanner in sorted({f["scanner"] for f in findings}):
        items = [f for f in findings if f["scanner"] == scanner]
        rules = sorted({f["rule"] for f in items})
        runs.append({
            "tool": {"driver": {"name": f"skill-kit-{scanner}", "informationUri": "https://github.com/",
                                "rules": [{"id": r, "shortDescription": {"text": r}} for r in rules]}},
            "results": [{
                "ruleId": f["rule"], "level": level[f["severity"]],
                "message": {"text": f"[{f['severity']}] {f['message']}"},
                "partialFingerprints": {"kitScan/v1": fingerprint(f)},
                "locations": [{"physicalLocation": {"artifactLocation": {"uri": f["file"].replace("\\", "/")},
                                                    "region": {"startLine": f["line"]}}}],
            } for f in items]})
    return {"$schema": "https://json.schemastore.org/sarif-2.1.0.json", "version": "2.1.0", "runs": runs}


def to_md(findings, counts, scanned, fail_on, failed, baselined):
    icon = {"CRITICAL": "🔴", "HIGH": "🔴", "MED": "🟠", "LOW": "⚪"}
    out = [f"## Skill-kit quality gate: {'❌ FAILED' if failed else '✅ PASSED'} (fail on {fail_on}+)", "",
           "| Scanner | Files | CRITICAL | HIGH | MED | LOW |", "|---|---|---|---|---|---|"]
    for s in SCANNERS:
        if s in scanned:
            c = counts.get(s, {})
            out.append(f"| {s} | {scanned[s]} | {c.get('CRITICAL', 0)} | {c.get('HIGH', 0)} | {c.get('MED', 0)} | {c.get('LOW', 0)} |")
    if baselined:
        out.append(f"\n_{baselined} finding(s) suppressed by baseline._")
    top = [f for f in findings if f["severity"] != "LOW"][:50]
    if top:
        out += ["", "| Sev | Scanner | Location | Rule | Message |", "|---|---|---|---|---|"]
        out += [f"| {icon[f['severity']]} {f['severity']} | {f['scanner']} | `{f['file']}:{f['line']}` | {f['rule']} | "
                f"{f['message'].replace('|', '/')[:140]} |" for f in top]
    out += ["", "_Heuristic leads: confirm each finding. Suppress a reviewed security line with `nosec`; "
                "rotate any real secret._"]
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser(add_help=True, usage=__doc__)
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--changed")
    ap.add_argument("--kit", default=str(Path(__file__).resolve().parent.parent / "plugins" / "agentic-skill-kit"))
    ap.add_argument("--fail-on", default="HIGH", type=str.upper)
    ap.add_argument("--only")
    ap.add_argument("--md")
    ap.add_argument("--sarif")
    ap.add_argument("--baseline")
    ap.add_argument("--write-baseline")
    a = ap.parse_args()
    kit = Path(a.kit)
    if not (kit / "skills").is_dir() or a.fail_on not in SEV_ORDER + ["NONE"]:
        print(__doc__)
        return 2
    names = [n for n in (a.only.split(",") if a.only else SCANNERS) if n in SCANNERS]
    files = git_changed(a.changed) if a.changed else collect(a.paths or ["."])
    files = [f for f in files if kit.resolve() not in f.resolve().parents]  # never scan the kit itself

    findings, scanned = [], {}
    for n in names:
        found, count = run(kit, n, files)
        findings += found
        scanned[n] = count
    if a.write_baseline:
        Path(a.write_baseline).write_text(json.dumps(sorted({fingerprint(f) for f in findings}), indent=1))
        print(f"kit_scan: wrote baseline with {len(findings)} finding(s) to {a.write_baseline}")
    accepted = set(json.loads(Path(a.baseline).read_text())) if a.baseline and Path(a.baseline).exists() else set()
    before = len(findings)
    findings = [f for f in findings if fingerprint(f) not in accepted]
    findings.sort(key=lambda f: (-SEV_ORDER.index(f["severity"]), f["file"], f["line"]))

    counts = {}
    for f in findings:
        counts.setdefault(f["scanner"], {}).setdefault(f["severity"], 0)
        counts[f["scanner"]][f["severity"]] += 1
    failed = a.fail_on != "NONE" and any(SEV_ORDER.index(f["severity"]) >= SEV_ORDER.index(a.fail_on) for f in findings)

    for f in findings:
        print(f"{f['file']}:{f['line']}  {f['severity']:<8} {f['scanner']:<11} {f['rule']:<22} {f['message'][:120]}")
    md = to_md(findings, counts, scanned, a.fail_on, failed, before - len(findings))
    print("\n" + md)
    if a.md:
        with open(a.md, "a", encoding="utf-8") as fh:
            fh.write(md)
    if a.sarif:
        Path(a.sarif).write_text(json.dumps(to_sarif(findings), indent=1))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
