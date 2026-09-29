#!/usr/bin/env python3
"""Heuristic security scan for code and config. Python 3 stdlib only. Defensive use only.

Rules (severity, CWE):
  CRITICAL aws-access-key        AKIA/ASIA access key id                          CWE-798
  CRITICAL private-key           -----BEGIN ... PRIVATE KEY-----                  CWE-321
  HIGH     hardcoded-password    password/pwd = "literal"                          CWE-798
  HIGH     conn-string-password  Password=/Pwd= inside a connection string         CWE-798
  HIGH     jwt-token             eyJ...eyJ...sig literal                           CWE-798
  HIGH     high-entropy-secret   key/secret/token var = high-entropy literal       CWE-798
  HIGH     sql-injection         SQL keyword + concat / f-string / interpolation   CWE-89
  HIGH     code-eval             eval( / exec( / new Function(                     CWE-95
  HIGH     angular-bypass        bypassSecurityTrust*                              CWE-79
  HIGH     insecure-deserialize  pickle.loads / BinaryFormatter / ObjectInputStream / TypeNameHandling.All  CWE-502
  HIGH     yaml-unsafe-load      yaml.load without SafeLoader / unsafe_load        CWE-502
  HIGH     tls-verify-off        verify=False / trust-all / callback => true       CWE-295
  HIGH     weak-password-hash    MD5/SHA1 on a password                            CWE-916
  HIGH     insecure-random       Random / Math.random / random.* for tokens/keys   CWE-338
  HIGH     cors-any-credentials  CORS any origin (or reflected) + credentials      CWE-942
  MED      react-dangerous-html  dangerouslySetInnerHTML without DOMPurify         CWE-79
  MED      dom-innerhtml         .innerHTML/.outerHTML = / document.write          CWE-79
  MED      debug-enabled         debug=True / DEBUG = True / debug="true"          CWE-489
  MED      sensitive-logging     log/print of password/token/passport/card         CWE-532
  LOW      cors-wildcard         CORS "*" (Verify: fine for public, no-cookie APIs) CWE-942
  LOW      weak-hash             MD5/SHA1 outside password context (Verify use)    CWE-328

Secrets are masked in output (first 4 chars + ****). Suppress a reviewed line with `nosec`.
Heuristic: expect false positives and misses (taint flow is not tracked). Label findings Verify
until confirmed in code. A secret found in history must be ROTATED, not just removed.

Usage:
  python3 sec_scan.py src/ config/        # scan folders recursively
  python3 sec_scan.py app.py --min HIGH   # only HIGH and CRITICAL
Exit code: 1 if any CRITICAL or HIGH, else 0.
"""
import math
import re
import sys
from collections import Counter
from pathlib import Path

EXTS = {".cs", ".java", ".kt", ".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".html", ".json", ".yml", ".yaml",
        ".xml", ".config", ".properties", ".env", ".ini", ".toml", ".sql", ".tf", ".sh", ".ps1", ".cfg"}
NAMES = {"Dockerfile", ".env", "docker-compose.yml"}
SKIP_DIRS = {"node_modules", ".git", "bin", "obj", "target", "dist", "build", ".venv", "venv", "__pycache__"}
SKIP_FILES = {"package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock", "packages.lock.json"}
TEST_PATH = re.compile(r"(^|[/._-])(tests?|spec|__tests__|e2e|fixtures?)([/._-]|$)|/test_\w+\.py$|tests?\.(cs|java)$", re.I)
NAME_NOT_SECRET = re.compile(r"(?i)(tag|name|header|field|param|label|url|uri|path|type|prefix|endpoint|id)\W*$")
SEV = {"LOW": 0, "MED": 1, "HIGH": 2, "CRITICAL": 3}

PLACEHOLDER = re.compile(r"^(\$\{|\{\{|%\(|\$\(|<|#\{|\*+$|x{4,}|\.\.\.)|example|placeholder|changeme_in_env|dummy|redacted|your[-_]", re.I)
ENV_REF = re.compile(r"os\.environ|os\.getenv|process\.env|Environment\.GetEnvironmentVariable|System\.getenv|"
                     r"\$\{[A-Z_]+|config\[|Configuration\[|@Value\(|GetSection\(|SecretClient|getSecret", re.I)

AWS = re.compile(r"\b((?:AKIA|ASIA)[0-9A-Z]{16})\b")
PRIVATE_KEY = re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP |ENCRYPTED )?PRIVATE KEY(?: BLOCK)?-----")
PASSWORD = re.compile(r"""(?i)\b[\w.-]*(?:password|passwd|pwd)\b["']?\s*[:=]\s*[@$]?(["'])([^"'\s]{4,})\1""")
PASSWORD_PROP = re.compile(r"""(?i)^\s*[\w.-]*(?:password|passwd|pwd)\s*[:=]\s*([^\s"'#;{}$<][^\s#;]{3,})\s*$""")
CONN = re.compile(r"(?i)\b(?:password|pwd)\s*=\s*([^;\"'\s{}$<][^;\"'\s]{2,})")
JWT = re.compile(r"\b(eyJ[A-Za-z0-9_-]{8,}\.eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,})")
SECRET_VAR = re.compile(r"""(?i)\b[\w.-]*(?:secret|token|api[_-]?key|apikey|access[_-]?key|private[_-]?key|client[_-]?secret|signing[_-]?key)\w*\b["']?\s*[:=]\s*[@$]?(["'])([^"'\s]{16,})\1""")

SQL_KW = re.compile(r"""(?i)["'`]\s*(?:[^"'`]*\b)?(select\s.+\sfrom|insert\s+into|update\s+\w+\s+set|delete\s+from)\b""")
SQL_BUILD = re.compile(r"""["'`]\s*\+\s*[\w(]|[\w)\]]\s*\+\s*["'`]|\b[rR]?[fF][rR]?"[^"]*\{|\b[rR]?[fF][rR]?'[^']*\{|\$@?"[^"]*\{|`[^`]*\$\{|["']\s*%\s*[\w(]|\.format\s*\(|String\.format\s*\(|\bconcat\s*\(""")
EVAL = re.compile(r"(?<![.\w])(eval|exec)\s*\(|\bnew\s+Function\s*\(|(?<![.\w])Function\s*\(\s*[\"'`]|\bsetTimeout\s*\(\s*[\"'`]")
ANGULAR = re.compile(r"\bbypassSecurityTrust(Html|Script|Style|Url|ResourceUrl)\s*\(")
DESER = re.compile(r"\b(c?[Pp]ickle|dill|shelve)\.(loads?|open)\s*\(|\bBinaryFormatter\b|\bNetDataContractSerializer\b|\bLosFormatter\b|"
                   r"\bSoapFormatter\b|\bObjectInputStream\b|TypeNameHandling\s*=\s*TypeNameHandling\.(All|Auto|Objects|Arrays)|"
                   r"\bjsonpickle\.decode\s*\(|\bmarshal\.loads?\s*\(|\bXMLDecoder\b|enableDefaultTyping\s*\(")
YAML_LOAD = re.compile(r"\byaml\.(load|load_all)\s*\((?!.*Loader\s*=\s*(yaml\.)?C?SafeLoader)|\byaml\.unsafe_load(_all)?\s*\(|Loader\s*=\s*(yaml\.)?(Unsafe)?Loader\b(?!.*Safe)")
TLS = re.compile(r"\bverify\s*=\s*False\b|TrustAll(Certs|Strategy|Manager)|trustAll(Certs|Manager)|\bNoopHostnameVerifier\b|"
                 r"ALLOW_ALL_HOSTNAME_VERIFIER|ServerCertificate(Custom)?ValidationCallback\s*[+=]+.*=>\s*true|"
                 r"DangerousAcceptAnyServerCertificateValidator|rejectUnauthorized\s*:\s*false|NODE_TLS_REJECT_UNAUTHORIZED\W+0|"
                 r"_create_unverified_context|\bCERT_NONE\b|InsecureSkipVerify\s*:\s*true|--insecure\b|curl\s+-k\b")
WEAK_HASH = re.compile(r"""(?i)\bmd5\b|\bsha-?1\b|MD5\.Create|SHA1\.Create|MD5CryptoServiceProvider|SHA1Managed|hashlib\.(md5|sha1)|getInstance\(\s*["'](MD5|SHA-?1)["']|createHash\(\s*["'](md5|sha1)["']|DigestUtils\.(md5|sha1)""")
PW_CONTEXT = re.compile(r"(?i)pass(word)?|pwd|credential")
WEAK_RANDOM = re.compile(r"\bnew\s+Random\s*\(|\bRandom\.Shared\b|\brandom\.(random|randint|choice|choices|randrange|getrandbits|sample)\s*\(|\bMath\.random\s*\(|\bRandomStringUtils\.random(Alphanumeric)?\s*\(|\bThreadLocalRandom\b")
TOKEN_CONTEXT = re.compile(r"(?i)token|secret|password|passwd|otp|nonce|salt|session|api[_-]?key|reset|csrf|verification|\bkey\b")
CORS_ANY = re.compile(r"""AllowAnyOrigin\s*\(|SetIsOriginAllowed\s*\(\s*\w*\s*=>\s*true|allow_origins\s*=\s*\[\s*["']\*["']|allowedOrigins\s*\(\s*["']\*["']|allowedOriginPatterns\s*\(\s*["']\*["']|"""
                      r"""@CrossOrigin\s*\(\s*(origins\s*=\s*)?["']\*["']|Access-Control-Allow-Origin["']?\s*[:,]\s*["']\*|origin\s*:\s*(["']\*["']|true)\b|CORS_ALLOW_ALL_ORIGINS\s*=\s*True|CORS_ORIGIN_ALLOW_ALL\s*=\s*True""")
CORS_CRED = re.compile(r"(?i)AllowCredentials\s*\(|allow_credentials\s*=\s*True|allowCredentials\s*\(\s*true|allowCredentials\s*=\s*[\"']true|credentials\s*:\s*true|Allow-Credentials[\"']?\s*[:,]\s*[\"']true|CORS_ALLOW_CREDENTIALS\s*=\s*True")
REACT_HTML = re.compile(r"dangerouslySetInnerHTML")
DOM_HTML = re.compile(r"\.(innerHTML|outerHTML)\s*\+?=(?!=)|\bdocument\.write(ln)?\s*\(|\.insertAdjacentHTML\s*\(")
DEBUG = re.compile(r"""(?i)\bdebug\s*[=:]\s*["']?true\b|\.run\s*\(.*debug\s*=\s*True|<compilation[^>]*debug\s*=\s*["']true|"""
                   r"""management\.endpoints\.web\.exposure\.include\s*[=:]\s*["']?\*|FLASK_DEBUG\s*=\s*1""")
LOG_CALL = re.compile(r"(?i)\b(log(ger)?|_logger|console|logging)\.(log|debug|info|warn(ing)?|error|trace|information|warning)\w*\s*\(|\bprint\s*\(|System\.out\.print|Console\.Write")
SENSITIVE = re.compile(r"(?i)password|passwd|\bpwd\b|secret|\btoken\b|access_?token|api_?key|passport|card_?number|\bcvv\b|\bpan\b|\bssn\b|date_?of_?birth|\bdob\b")

INFO = {
    "aws-access-key": ("CRITICAL", "CWE-798", "AWS access key in source: rotate in IAM now, then load from a secret store"),
    "private-key": ("CRITICAL", "CWE-321", "Private key committed: revoke/rotate the key pair; store in Key Vault / Secrets Manager"),
    "hardcoded-password": ("HIGH", "CWE-798", "Hard-coded password: rotate it and read from env / secret store"),
    "conn-string-password": ("HIGH", "CWE-798", "Password in connection string: use managed identity / secret store; rotate"),
    "jwt-token": ("HIGH", "CWE-798", "JWT literal in code/config: remove, revoke if real, rotate signing key if it was a key"),
    "high-entropy-secret": ("HIGH", "CWE-798", "High-entropy value assigned to a secret-like name (Verify): move to secret store; rotate"),
    "sql-injection": ("HIGH", "CWE-89", "SQL built from strings: use parameters / prepared statements (Verify input source)"),
    "code-eval": ("HIGH", "CWE-95", "Dynamic code execution: remove; use a parser / lookup table / JSON.parse"),
    "angular-bypass": ("HIGH", "CWE-79", "Angular sanitizer bypassed: sanitize or bind as text; bypass only constant trusted values"),
    "insecure-deserialize": ("HIGH", "CWE-502", "Unsafe deserializer on possibly untrusted data: use JSON with a fixed type / allow-list"),
    "yaml-unsafe-load": ("HIGH", "CWE-502", "yaml.load without SafeLoader can build arbitrary objects: use yaml.safe_load"),
    "tls-verify-off": ("HIGH", "CWE-295", "TLS certificate validation disabled: remove; trust a specific CA bundle instead"),
    "weak-password-hash": ("HIGH", "CWE-916", "MD5/SHA1 for passwords: use Argon2id / bcrypt / PBKDF2 (framework hasher)"),
    "insecure-random": ("HIGH", "CWE-338", "Non-crypto RNG for a security value: use RandomNumberGenerator / SecureRandom / secrets / crypto.getRandomValues"),
    "cors-any-credentials": ("HIGH", "CWE-942", "Any/reflected origin with credentials: allow-list exact origins"),
    "react-dangerous-html": ("MED", "CWE-79", "dangerouslySetInnerHTML: render text, or sanitize with DOMPurify first (Verify source)"),
    "dom-innerhtml": ("MED", "CWE-79", "HTML sink: use textContent / framework binding, or sanitize (Verify source)"),
    "debug-enabled": ("MED", "CWE-489", "Debug mode / exposed actuator: disable in production config"),
    "sensitive-logging": ("MED", "CWE-532", "Sensitive field in log/print (Verify): log IDs only, mask PII / secrets"),
    "cors-wildcard": ("LOW", "CWE-942", "CORS allows any origin (Verify: acceptable only for public, cookie-less APIs)"),
    "weak-hash": ("LOW", "CWE-328", "MD5/SHA1 (Verify): fine for non-security checksums, not for integrity/signatures/passwords"),
}


def entropy(s):
    counts = Counter(s)
    return -sum(c / len(s) * math.log2(c / len(s)) for c in counts.values())


def mask(value):
    return value[:4] + "****"


def redact(line):
    """Mask every secret-looking value in a line before printing it."""
    out = AWS.sub(lambda m: mask(m.group(1)), line)
    out = JWT.sub(lambda m: mask(m.group(1)), out)
    for rx in (PASSWORD, SECRET_VAR):
        out = rx.sub(lambda m: m.group(0).replace(m.group(2), mask(m.group(2))), out)
    out = CONN.sub(lambda m: m.group(0).replace(m.group(1), mask(m.group(1))), out)
    m = PASSWORD_PROP.match(out)
    if m and "****" not in out:
        out = out.replace(m.group(1), mask(m.group(1)))
    return out


def real_secret(value, line):
    return not PLACEHOLDER.search(value) and not ENV_REF.search(line)


def scan_file(path):
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        print(f"{path}: cannot read ({e})", file=sys.stderr)
        return []
    lines = text.splitlines()
    ext = path.suffix.lower()
    code_file = ext in {".cs", ".java", ".kt", ".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".html"}
    file_cors_cred = bool(CORS_CRED.search(text))
    findings = []
    in_test = bool(TEST_PATH.search("/" + path.as_posix()))
    for no, line in enumerate(lines, 1):
        if "nosec" in line or "sec-scan: ignore" in line:
            continue
        stripped = line.strip()
        is_comment = stripped.startswith(("//", "#", "*", "/*", "--", "<!--")) and not PRIVATE_KEY.search(line)
        hits = []
        if (m := AWS.search(line)) and not m.group(1).endswith("EXAMPLE"):  # AWS docs sample key is ignored
            hits.append("aws-access-key")  # checked in comments too: a key in a comment still leaks
        if PRIVATE_KEY.search(line):
            hits.append("private-key")
        if not is_comment:
            pw = PASSWORD.search(line) or (not code_file and PASSWORD_PROP.match(line))
            pw_val = (pw.group(2) if pw and pw.re is PASSWORD else pw.group(1)) if pw else ""
            if pw and real_secret(pw_val, line):
                hits.append("hardcoded-password")
            elif ";" in line and (c := CONN.search(line)) and re.search(r"(?i)(server|data source|host|user id|uid|username)\s*=", line) \
                    and real_secret(c.group(1), line):
                hits.append("conn-string-password")
            if JWT.search(line):
                hits.append("jwt-token")
            if (s := SECRET_VAR.search(line)) and real_secret(s.group(2), line) and entropy(s.group(2)) >= 3.5 \
                    and not NAME_NOT_SECRET.search(line[:s.start(1)].rstrip(" :=\"'@$")) \
                    and "jwt-token" not in hits and "aws-access-key" not in hits:
                hits.append("high-entropy-secret")
            if SQL_KW.search(line) and SQL_BUILD.search(line):
                hits.append("sql-injection")
            if code_file and EVAL.search(line):
                hits.append("code-eval")
            if ANGULAR.search(line):
                hits.append("angular-bypass")
            if DESER.search(line) and not re.match(r"\s*(import|using|from)\s", line):
                hits.append("insecure-deserialize")
            if YAML_LOAD.search(line):
                hits.append("yaml-unsafe-load")
            if TLS.search(line) and not re.search(r"(?i)verify\s*=\s*False.*#.*test", line):
                hits.append("tls-verify-off")
            if WEAK_HASH.search(line):
                hits.append("weak-password-hash" if PW_CONTEXT.search(line) else "weak-hash")
            if WEAK_RANDOM.search(line) and TOKEN_CONTEXT.search(line):
                hits.append("insecure-random")
            if CORS_ANY.search(line):
                hits.append("cors-any-credentials" if file_cors_cred else "cors-wildcard")
            if REACT_HTML.search(line) and "DOMPurify" not in line and "sanitize" not in line.lower():
                hits.append("react-dangerous-html")
            if DOM_HTML.search(line) and "sanitize" not in line.lower() and "DOMPurify" not in line:
                hits.append("dom-innerhtml")
            if DEBUG.search(line):
                hits.append("debug-enabled")
            outside_text = re.sub(r"(\"|')(?:(?!\1).)*\1", lambda m: " ".join(re.findall(r"\{([^}]*)\}", m.group(0))), line)
            if code_file and LOG_CALL.search(line) and SENSITIVE.search(outside_text) and not re.search(r"(?i)mask|redact|\*\*\*", line):
                hits.append("sensitive-logging")
        for rule in dict.fromkeys(hits):
            sev, cwe, msg = INFO[rule]
            if in_test and sev in ("HIGH", "MED"):
                sev, msg = "LOW", "(test code: Verify it is only a fixture) " + msg
            findings.append((str(path), no, sev, rule, cwe, msg, redact(stripped)[:140]))
    return findings


def iter_files(args):
    for a in args:
        p = Path(a)
        if p.is_dir():
            for f in sorted(p.rglob("*")):
                if f.is_file() and (f.suffix.lower() in EXTS or f.name in NAMES or f.name.startswith(".env")) \
                        and f.name not in SKIP_FILES and not SKIP_DIRS.intersection(f.parts):
                    yield f
        elif p.is_file():
            yield p
        else:
            print(f"{a}: not found", file=sys.stderr)


def main(argv):
    minimum = "LOW"
    if "--min" in argv:
        i = argv.index("--min")
        minimum = argv[i + 1].upper() if i + 1 < len(argv) else ""
        argv = argv[:i] + argv[i + 2:]
    if not argv or minimum not in SEV:
        sys.exit(__doc__)
    files = list(iter_files(argv))
    files = [f for f in files if f.resolve() != Path(__file__).resolve()]  # skip own rule definitions
    found = [f for p in files for f in scan_file(p) if SEV[f[2]] >= SEV[minimum]]
    found.sort(key=lambda x: (-SEV[x[2]], x[0], x[1]))
    for file, no, sev, rule, cwe, msg, snippet in found:
        print(f"{file}:{no}  {sev:<8} {rule:<21} {cwe:<8} {msg}\n    > {snippet}")
    counts = Counter(f[2] for f in found)
    print(f"\nScanned {len(files)} file(s): " + ", ".join(f"{counts.get(s, 0)} {s}" for s in ("CRITICAL", "HIGH", "MED", "LOW"))
          + ". Heuristic - confirm each finding; secrets masked; rotate any real exposed secret.")
    return 1 if counts.get("CRITICAL") or counts.get("HIGH") else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
