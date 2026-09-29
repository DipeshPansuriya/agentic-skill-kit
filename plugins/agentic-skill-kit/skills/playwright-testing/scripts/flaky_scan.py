#!/usr/bin/env python3
"""Scan Playwright test files for flakiness and hygiene smells. Python 3 stdlib only.

Checks (.ts .tsx .js .mjs .cjs .py):
  ERROR  hard-wait        waitForTimeout / wait_for_timeout / sleep / Task.Delay-style waits
  ERROR  only             test.only / describe.only / it.only committed
  ERROR  missing-await    expect(...) web-first matcher or page action without await (TS/JS)
  ERROR  hardcoded-secret password/token/api key literal, or literal typed into a password field
  WARN   brittle-selector XPath, nth-child / nth-of-type, long CSS child chains
  WARN   force-click      { force: true } / force=True hides actionability problems
  WARN   non-web-first    expect(await x.isVisible()/textContent()) does not retry
  WARN   hardcoded-url    absolute http(s) URL other than localhost (use baseURL / env)

Heuristic: confirm each finding in the code.

Usage:
  python3 flaky_scan.py tests/                 # scan a folder recursively
  python3 flaky_scan.py a.spec.ts b_test.py    # scan files
  python3 flaky_scan.py tests/ --min ERROR     # only errors
Exit code: 1 if any ERROR, else 0.
"""
import re
import sys
from pathlib import Path

EXTS = {".ts", ".tsx", ".js", ".mjs", ".cjs", ".py"}
SKIP_DIRS = {"node_modules", ".git", "playwright-report", "test-results", "dist", ".venv", "venv"}
SEV = {"INFO": 0, "WARN": 1, "ERROR": 2}

MATCHERS = (r"toBeVisible|toBeHidden|toHaveText|toContainText|toHaveURL|toHaveTitle|toHaveCount|"
            r"toHaveValue|toHaveValues|toHaveAttribute|toHaveClass|toHaveCSS|toHaveId|toHaveJSProperty|"
            r"toBeChecked|toBeEnabled|toBeDisabled|toBeEditable|toBeEmpty|toBeFocused|toBeAttached|"
            r"toBeInViewport|toHaveScreenshot|toMatchAriaSnapshot|toHaveAccessibleName|"
            r"toHaveAccessibleDescription|toHaveRole|toBeOK")
ACTIONS = (r"goto|click|dblclick|fill|press|pressSequentially|type|check|uncheck|selectOption|hover|"
           r"tap|focus|setInputFiles|dragTo|reload|goBack|goForward|waitForURL|waitForLoadState|"
           r"waitForSelector|route|unroute|setViewportSize|clear")
FAKE_VALUE = re.compile(r"wrong|invalid|incorrect|not-the|fake|dummy|bad|x{3,}|\$\{|process\.env", re.I)

RULES = [
    ("ERROR", "hard-wait", re.compile(r"\bwaitForTimeout\s*\(|\bwait_for_timeout\s*\(|\btime\.sleep\s*\(|\basyncio\.sleep\s*\(|"
                                      r"\bThread\.sleep\s*\(|\bTask\.Delay\s*\(|new\s+Promise\s*\(\s*\(?\s*\w+\s*\)?\s*=>\s*setTimeout"),
     "Hard wait: replace with a web-first assertion or wait for the specific response/URL/state"),
    ("ERROR", "only", re.compile(r"\b(?:test|it|describe)(?:\.describe)?\.only\s*\("),
     "Focused test committed: remove .only (use forbidOnly: !!process.env.CI)"),
    ("WARN", "force-click", re.compile(r"\bforce\s*:\s*true\b|\bforce\s*=\s*True\b"),
     "force skips actionability checks and hides real bugs (overlay, disabled, not yet hydrated): fix the cause"),
    ("WARN", "non-web-first", re.compile(r"expect\s*\(\s*await\s+[^;]*?\.(?:isVisible|isHidden|isEnabled|isChecked|textContent|innerText|inputValue|getAttribute|count)\s*\("),
     "Snapshot check does not retry: use await expect(locator).toBeVisible()/toHaveText()/toHaveCount()"),
]
STRING = re.compile(r"""(['"`])((?:\\.|(?!\1).)*)\1""")
SECRET_ASSIGN = re.compile(r"""\b\w*(?:password|passwd|pwd|secret|token|api[_-]?key|client[_-]?secret)\w*\s*[:=]\s*(['"`])([^'"`]{3,})\1""", re.I)
PASSWORD_FILL = re.compile(r"""(?:pass(?:word)?|pwd)[^)]*\)\s*\.fill\s*\(\s*(['"`])([^'"`]+)\1|\.fill\s*\(\s*(['"`])[^'"`]*pass(?:word)?[^'"`]*\3\s*,\s*(['"`])([^'"`]+)\4""", re.I)
BEARER = re.compile(r"""['"`]Bearer\s+[A-Za-z0-9._\-]{8,}""")
URL = re.compile(r"""['"`](https?://[^'"`\s]+)""")
MISSING_AWAIT_EXPECT = re.compile(r"(?<![\w.])expect(?:\.soft)?\s*\((?:[^;]*?)\)\s*(?:\.not)?\s*\.(?:" + MATCHERS + r")\s*\(")
ACTION_STMT = re.compile(r"^(?:this\.)?(?:\w*page\w*|\w+Page|locator|\w+Locator)\b[\w.]*(?:\([^;]*\))?[\w.()'\"\s,{}:]*\.(?:" + ACTIONS + r")\s*\(", re.I)


def brittle(literal):
    s = literal.strip()
    if s.startswith(("//", "xpath=", "(//")):
        return "XPath selector: use getByRole/getByLabel/getByTestId"
    if re.search(r":nth-(?:child|of-type)\(", s):
        return "Positional CSS (nth-child/nth-of-type): breaks when order changes; use role/text filters"
    if s.count(">") >= 3 and re.fullmatch(r"[\w\s.#>:()\[\]=\"'-]+", s):
        return "Long CSS child chain couples the test to DOM structure: use a user-facing locator"
    return None


def scan_file(path):
    findings = []
    is_py = path.suffix == ".py"
    for no, raw in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith(("//", "/*", "*", "#")):
            continue
        for sev, rule, rx, msg in RULES:
            if rx.search(line):
                findings.append((no, sev, rule, msg))
        for m in STRING.finditer(line):
            why = brittle(m.group(2))
            if why:
                findings.append((no, "WARN", "brittle-selector", why))
                break
        for m in URL.finditer(line):
            if not re.match(r"https?://(localhost|127\.0\.0\.1|0\.0\.0\.0)(:\d+)?(/|$)", m.group(1)):
                findings.append((no, "WARN", "hardcoded-url", f"Hard-coded URL {m.group(1)}: use baseURL / env var and relative paths"))
                break
        secret = None
        m = SECRET_ASSIGN.search(line)
        if m and not FAKE_VALUE.search(m.group(2)):
            secret = "Credential literal in test code: read from env / CI secret store"
        m = PASSWORD_FILL.search(line)
        if m:
            val = m.group(2) or m.group(5) or ""
            if not FAKE_VALUE.search(val):
                secret = "Password typed from a literal: use process.env.E2E_PASSWORD (or os.environ)"
        if BEARER.search(line):
            secret = "Hard-coded bearer token: inject from env / CI secret store"
        if secret:
            findings.append((no, "ERROR", "hardcoded-secret", secret))
        if not is_py:
            starts_ok = re.match(r"^(?:await|return|const|let|var|yield)\b|^[\w.]+\s*=(?!=)|^\)|^\.|^\w+\s*:", line)
            if MISSING_AWAIT_EXPECT.search(line) and not re.search(r"\bawait\s+expect", line) and not starts_ok:
                findings.append((no, "ERROR", "missing-await", "expect(...) web-first assertion without await: it never fails the test"))
            elif ACTION_STMT.search(line) and not starts_ok:
                findings.append((no, "ERROR", "missing-await", "Page/locator action without await: races the next step"))
    return findings


def collect(args):
    for a in args:
        p = Path(a)
        if p.is_dir():
            for f in sorted(p.rglob("*")):
                if f.is_file() and f.suffix in EXTS and not SKIP_DIRS.intersection(f.parts):
                    yield f
        elif p.is_file():
            yield p
        else:
            print(f"skip: {a} not found", file=sys.stderr)


def main(argv):
    args = argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if args else 2
    min_sev = "INFO"
    if "--min" in args:
        k = args.index("--min")
        min_sev = args[k + 1].upper() if k + 1 < len(args) else "INFO"
        del args[k:k + 2]
    total = {"ERROR": 0, "WARN": 0, "INFO": 0}
    files = 0
    for f in collect(args):
        files += 1
        for no, sev, rule, msg in sorted(scan_file(f), key=lambda r: (r[0], -SEV[r[1]])):
            if SEV[sev] >= SEV.get(min_sev, 0):
                total[sev] += 1
                print(f"{f}:{no}: {sev:<5} [{rule}] {msg}")
    print(f"-- {files} file(s): {total['ERROR']} error(s), {total['WARN']} warning(s), {total['INFO']} info")
    return 1 if total["ERROR"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
