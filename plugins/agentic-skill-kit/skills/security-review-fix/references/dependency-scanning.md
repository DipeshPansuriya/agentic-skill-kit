# Dependency Scanning & Security Tooling

## Vulnerable dependency commands (SCA)
| Ecosystem | Command | Notes |
|---|---|---|
| .NET | `dotnet list package --vulnerable --include-transitive` | Uses NuGet advisory data (GitHub Advisory DB). NuGet audit also runs on restore (`<NuGetAudit>true</NuGetAudit>`, `<NuGetAuditMode>all</NuGetAuditMode>` for transitive) |
| .NET (outdated) | `dotnet list package --outdated` | Upgrade plan input |
| npm | `npm audit --omit=dev` ; fix: `npm audit fix` (no `--force` without review) | `--force` may apply breaking major upgrades |
| pnpm / yarn | `pnpm audit` / `yarn npm audit` (Berry) | |
| Python | `pip-audit` (`pip-audit -r requirements.txt`) ; `uv pip compile` + pip-audit | Uses PyPI advisory / OSV data |
| Java (Maven) | `mvn org.owasp:dependency-check-maven:check` | Set an NVD API key for speed; `failBuildOnCVSS=7` |
| Java (Gradle) | `./gradlew dependencyCheckAnalyze` (plugin `org.owasp.dependencycheck`) | |
| Any (lock files, SBOM) | `osv-scanner scan -r .` ; `trivy fs .` ; `grype dir:.` | Multi-ecosystem |
| Containers | `trivy image registry/app:tag` | OS packages + app deps |
| SBOM | `syft . -o cyclonedx-json`, `dotnet CycloneDX`, `cyclonedx-maven-plugin`, `cyclonedx-py` | Needed for A03:2025 supply-chain evidence |

## Triage rules for a vulnerable package
| Situation | Action |
|---|---|
| Fixed version exists, patch/minor bump | Upgrade now; run tests |
| Fix requires major upgrade | Plan upgrade; meanwhile check reachability and add a compensating control; record as residual risk |
| Transitive dependency | Upgrade the parent; else pin/override (`<PackageReference>` direct pin in .NET, `overrides` in npm, `dependencyManagement` in Maven, constraints file in pip) |
| No fix available | Check if vulnerable function is reachable; mitigate (WAF rule, input validation, disable feature); track advisory |
| Dev-only dependency | Lower priority unless it runs in CI with secrets |
| Abandoned package | Replace |

## SAST / secrets / IaC tools
| Tool | Type | Command | Good for |
|---|---|---|---|
| Semgrep | SAST (pattern + taint) | `semgrep scan --config p/owasp-top-ten --config p/secrets` | Fast, custom rules, all stacks |
| CodeQL | SAST (dataflow) | GitHub code scanning; `codeql database create` + `codeql database analyze` | Deep taint tracking: C#, Java, Python, JS/TS |
| SonarQube / SonarCloud | SAST + quality gates | `dotnet sonarscanner`, `mvn sonar:sonar`, `sonar-scanner` | Security hotspots, PR decoration |
| gitleaks | Secrets | `gitleaks git -v` (history) / `gitleaks dir .` (v8.19+) ; pre-commit hook | Secrets in code and history |
| trufflehog | Secrets (verifies live keys) | `trufflehog git file://. --only-verified` | Confirms which leaked keys are active |
| Trivy | SCA + IaC + image + secrets | `trivy fs --scanners vuln,secret,misconfig .` | One tool for containers, Terraform, k8s |
| Checkov / tfsec (now in Trivy) | IaC | `checkov -d infra/` | Terraform, CloudFormation, k8s, Dockerfile |
| Bandit | Python SAST | `bandit -r src -ll` | Python-specific issues |
| SpotBugs + FindSecBugs | Java SAST | Maven/Gradle plugin | Java bytecode checks |
| .NET analyzers | C# SAST | `<AnalysisMode>All</AnalysisMode>`, security rules CA2100, CA3001-CA3012, CA5350/CA5351 | Built into the SDK |
| eslint-plugin-security / eslint-plugin-no-unsanitized | JS/TS | ESLint config | DOM sinks, eval |
| OWASP ZAP | DAST | `zap-baseline.py -t https://staging...` (staging only, with authorization) | Headers, runtime misconfig |

`scripts/sec_scan.py` is a quick heuristic pre-check, not a replacement for these tools.
