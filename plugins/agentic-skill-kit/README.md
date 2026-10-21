# agentic-skill-kit (v1.0.0)

A plugin of 32 skills that Claude uses automatically when a request matches. There are no connectors or setup steps.

| Group | Skills |
|---|---|
| Building skills | create-skill, combine-skills, benchmark-skill |
| Delivery | incident-rca, requirements-to-stories, release-notes, test-cases-from-requirements |
| Engineering | code-review, software-architecture, workflow-design, backend-engineering (.NET, Java, Python), frontend-engineering (React, Angular), database-engineering (MS-SQL, PostgreSQL, NoSQL), sql-performance-tuning, code-performance, refactoring, security-review-fix, playwright-testing, multitenant-playwright |

## Before first use
- **refactoring:** uses the ponytail plugin if it's installed, and asks before installing it if not.

## Branding
Reports, documents, emails and slides use neutral formatting. A brand or company design skill is applied only when you name it in your request.

## Quality
- All 32 skills pass the kit validator.
- Every skill has `evals/test-cases.md`, including cases where it should not trigger.
- The scanners were tuned on real open-source repos.
- The CI/CD gate lives in the repository's `ci/` folder. Optional safety hooks are in the `agentic-skill-kit-guard` plugin.
