# Agentic Skill Kit

A Claude Code plugin marketplace with **39 skills** for day-to-day engineering and work communication. It also includes an optional **guard** plugin with safety hooks, a **CI/CD quality gate**, and guides on how to build and benchmark your own skills.

## Install (Claude Code / VS Code / Cursor)

```text
/plugin marketplace add DipeshPansuriya/agentic-skill-kit
/plugin install agentic-skill-kit@dipesh-skills
/plugin install agentic-skill-kit-guard@dipesh-skills   # optional safety hooks
```

Skills load automatically when a request matches. You can also call one directly, e.g. `/agentic-skill-kit:sql-performance-tuning`.

## What's inside

### Plugin: `agentic-skill-kit`
| Group | Skills |
|---|---|
| **Delivery** | `requirements-to-stories`, `release-notes`, `test-cases-from-requirements |
| **Engineering** | `code-review`, `software-architecture` (incl. design patterns), `workflow-design`, `backend-engineering` (.NET, Java, Python), `frontend-engineering` (React, Angular), `database-engineering` (MS-SQL, PostgreSQL, NoSQL), `sql-performance-tuning`, `code-performance`, `refactoring`, `security-review-fix`, `playwright-testing` |
| **UI / store** | `web-design`, `modern-enterprise-ui`, `anatomy, `video-avatar`, `room-redesign` |
| **Spec Kit** | `speckit-specify`, `speckit-plan`, `speckit-tasks`, `speckit-implement`, `speckit-analyze`, `speckit-clarify`, `speckit-checklist`, `speckit-constitution`, `speckit-converge`, `speckit-taskstoissues` |
| **Data / integration** | `stack-java-spring-react`, `database-engineering`, `sql-performance-tuning` |
| **Guidelines / GTM / pentest** | `karpathy-guidelines |

Each skill has a `SKILL.md`. Most also have `references/`, `templates/`, helper `scripts/` (Python 3, standard library) and `evals/test-cases.md`, which includes requests the skill should *not* trigger on.

### Plugin: `agentic-skill-kit-guard` (optional)
| Hook | What it does |
|---|---|
| After Write/Edit | Runs a local security scan (and a SQL lint for `.sql`) on the edited file, then asks Claude to fix HIGH findings |
| Before `git commit` | Blocks the commit if staged files contain likely secrets (values are masked in output) |

The guard is local only: no network calls and no data leaves your machine. Uninstall it at any time with `/plugin uninstall agentic-skill-kit-guard@dipesh-skills`.

### CI/CD quality gate: [`ci/`](ci/README.md)
Runs the security, performance, SQL and Playwright scanners on pull requests, in GitHub Actions or Azure DevOps. It writes a markdown summary and SARIF output, supports a baseline for existing repos, and fails the build on HIGH findings.

### Guides: [`guides/`](guides/)
How to create a skill, combine skills, and benchmark a skill.

## Design principles
- **Never invent data.** Missing facts become `TBD` and are listed under *Needs input*.
- **Measure, don't guess.** Performance and refactoring work requires before/after numbers.
- **Behaviour preserved.** Refactoring requires a safety net (tests, or a result-set comparison for SQL).
- **Branding only on request.** Output uses neutral formatting unless you name a brand or design skill.
- **Heuristic scanners are leads, not verdicts.** Confirm findings; they complement CodeQL, SonarQube and dependency scanners, they don't replace them.

## Requirements
- Claude Code (CLI, VS Code or Cursor extension)
- Python 3.10+ for the helper scripts

## Contributing and security
- [CONTRIBUTING.md](CONTRIBUTING.md) explains how to propose changes. Every PR runs the validation workflow.
- [SECURITY.md](SECURITY.md) explains how to report a vulnerability privately.

## License
[MIT](LICENSE) © 2026 Dipesh Pansuriya
