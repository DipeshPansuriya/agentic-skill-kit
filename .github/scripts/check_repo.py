#!/usr/bin/env python3
"""Repository checks used by CI and locally: python .github/scripts/check_repo.py

1. Marketplace + plugin manifests are valid and names match
2. Every skill passes validate_skill.py
3. Scanner self-tests: bad samples trigger, clean samples stay silent
4. Other helper scripts run on their samples
5. Guard hooks behave (block on secret, pass on clean)
6. No secret-shaped strings are committed anywhere in the repo
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KIT = ROOT / "plugins" / "agentic-skill-kit"
SK = KIT / "skills"
GUARD = ROOT / "plugins" / "agentic-skill-kit-guard"
PY = sys.executable
failures = []


def check(name, ok, detail=""):
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not ok else ""))
    if not ok:
        failures.append(name)


def run(*args, stdin=None, cwd=None):
    return subprocess.run([PY, *map(str, args)], capture_output=True, text=True, input=stdin, cwd=cwd)


# 1. manifests
market = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())
check("marketplace has name/owner/plugins", all(k in market for k in ("name", "owner", "plugins")))
for entry in market["plugins"]:
    pj = ROOT / entry["source"] / ".claude-plugin/plugin.json"
    manifest = json.loads(pj.read_text()) if pj.exists() else {}
    check(f"plugin {entry['name']} manifest name matches entry", manifest.get("name") == entry["name"])
    check(f"plugin {entry['name']} has semver version", bool(re.fullmatch(r"\d+\.\d+\.\d+", manifest.get("version", ""))))
hooks = json.loads((GUARD / "hooks/hooks.json").read_text())
check("guard hooks.json has PostToolUse and PreToolUse", {"PostToolUse", "PreToolUse"} <= set(hooks.get("hooks", {})))

# 2. skills
validator = SK / "create-skill/scripts/validate_skill.py"
skills = sorted(d for d in SK.iterdir() if d.is_dir())
bad = [d.name for d in skills if run(validator, d).returncode != 0]
check(f"all {len(skills)} skills pass validate_skill.py", not bad, ", ".join(bad))

# 3. scanner self-tests
with tempfile.TemporaryDirectory() as tmp:
    samples = SK / "security-review-fix/templates/samples"
    run(samples / "render_samples.py", tmp)
    sec = SK / "security-review-fix/scripts/sec_scan.py"
    for f in sorted(Path(tmp).iterdir()):
        r = run(sec, f)
        if f.name.startswith(("bad", "Bad")):
            check(f"sec_scan flags {f.name}", r.returncode == 1)
        elif f.name.startswith("clean"):
            check(f"sec_scan silent on {f.name}", r.returncode == 0 and "0 CRITICAL, 0 HIGH, 0 MED, 0 LOW" in r.stdout)

perf = SK / "code-performance/scripts/perf_smells.py"
for f in sorted((SK / "code-performance/templates/samples").iterdir()):
    r = run(perf, f)
    if f.name.lower().startswith("bad"):
        check(f"perf_smells flags {f.name}", " 0 HIGH, 0 MED, 0 LOW" not in r.stdout)
    elif f.name.startswith("clean"):
        check(f"perf_smells silent on {f.name}", "0 HIGH, 0 MED, 0 LOW" in r.stdout)

r = run(SK / "sql-performance-tuning/scripts/sql_lint.py", SK / "database-engineering/templates/sample-bad.sql")
check("sql_lint flags sample-bad.sql", "error(s)" in r.stdout and not r.stdout.strip().endswith("0 error(s), 0 warning(s), 0 info"))
flaky = SK / "playwright-testing/scripts/flaky_scan.py"
check("flaky_scan flags bad-example.spec.ts", "0 error(s)" not in run(flaky, SK / "playwright-testing/templates/bad-example.spec.ts").stdout)
check("flaky_scan silent on example.spec.ts", "0 error(s), 0 warning(s)" in run(flaky, SK / "playwright-testing/templates/example.spec.ts").stdout)

# 4. other helpers
for plan in sorted((SK / "sql-performance-tuning/templates").glob("sample-plan-*")):
    check(f"plan_analyzer runs on {plan.name}", "High" in run(SK / "sql-performance-tuning/scripts/plan_analyzer.py", plan).stdout)
check("validate_state_machine passes template",
      "PASS" in run(SK / "workflow-design/scripts/validate_state_machine.py", SK / "workflow-design/templates/state-machine-template.md").stdout)
check("code_metrics --compare runs",
      run(SK / "refactoring/scripts/code_metrics.py", "--compare", SK / "refactoring/templates/samples/python_before.py",
          SK / "refactoring/templates/samples/python_after.py").returncode == 0)
check("refactoring python sample is behaviour-equivalent",
      "mismatches=0" in run("check_python_equivalence.py", cwd=SK / "refactoring/templates/samples").stdout)
check("week_info runs", "ISO week" in run(SK / "weekly-status-report/scripts/week_info.py", "2026-01-01").stdout)

# 5. guard hooks
guard = GUARD / "hooks/guard.py"
with tempfile.TemporaryDirectory() as tmp:
    t = Path(tmp)
    (t / "bad.py").write_text('db_password = "' + "Sup3r" + 'S3cretValue!"\n')
    (t / "ok.py").write_text("x = 1\n")
    edit = lambda f: json.dumps({"tool_name": "Write", "tool_input": {"file_path": str(t / f)}})
    check("guard post-edit flags secret", run(guard, "post-edit", stdin=edit("bad.py")).returncode == 2)
    check("guard post-edit passes clean file", run(guard, "post-edit", stdin=edit("ok.py")).returncode == 0)
    subprocess.run(["git", "init", "-q"], cwd=t)
    subprocess.run(["git", "add", "bad.py"], cwd=t)
    commit = json.dumps({"tool_name": "Bash", "cwd": str(t), "tool_input": {"command": "git commit -m x"}})
    check("guard pre-commit blocks staged secret", run(guard, "pre-commit", stdin=commit).returncode == 2)
    check("guard ignores non-commit commands",
          run(guard, "pre-commit", stdin=json.dumps({"tool_input": {"command": "ls"}})).returncode == 0)

# 6. no secret-shaped strings committed
SECRET = re.compile(r"(AKIA|ASIA)[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9]{36}|"
                    r"xox[abprs]-[A-Za-z0-9-]{10,}|eyJ[A-Za-z0-9_-]{8,}\.eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}")
hits = [str(p.relative_to(ROOT)) for p in ROOT.rglob("*")
        if p.is_file() and ".git" not in p.parts and p.suffix not in {".png", ".jpg", ".zip"}
        and p != Path(__file__).resolve() and SECRET.search(p.read_text(errors="ignore"))]
check("no secret-shaped strings in repo", not hits, ", ".join(hits))

print(f"\n{'ALL CHECKS PASSED' if not failures else f'{len(failures)} CHECK(S) FAILED'}")
sys.exit(1 if failures else 0)
