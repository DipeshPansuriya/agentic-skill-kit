# agentic-skill-kit (v1.0.0)

A plugin of 24 skills that Claude uses automatically when a request matches. There are no connectors or setup steps.

| Group | Skills |
|---|---|
| Building skills | create-skill, combine-skills, benchmark-skill |
| Comms | weekly-status-report, meeting-notes-actions, sop-writer, rfp-answers |
| Delivery | incident-rca, requirements-to-stories, release-notes, test-cases-from-requirements, kpi-analysis |
| Engineering | code-review, software-architecture, workflow-design, backend-engineering (.NET, Java, Python), frontend-engineering (React, Angular), database-engineering (MS-SQL, PostgreSQL, NoSQL), sql-performance-tuning, code-performance, refactoring, security-review-fix, playwright-testing |

## Before first use
- **rfp-answers:** fill `skills/rfp-answers/references/answer-bank.md` with approved product facts. Until then, answers come back as "Needs input".
- **kpi-analysis:** its script needs pandas.
- **refactoring:** uses the ponytail plugin if it's installed, and asks before installing it if not.
- **Overlap with built-in skills:** skill-creator, internal-comms and doc-coauthoring overlap with create-skill/benchmark-skill, weekly-status-report/incident-rca and sop-writer. Turn the built-in ones off if the wrong skill is used.

## Branding
Reports, documents, emails and slides use neutral formatting. A brand or company design skill is applied only when you name it in your request.

## Quality
- All 24 skills pass the kit validator.
- Every skill has `evals/test-cases.md`, including cases where it should not trigger.
- The scanners were tuned on real open-source repos.
- The CI/CD gate lives in the repository's `ci/` folder. Optional safety hooks are in the `agentic-skill-kit-guard` plugin.
