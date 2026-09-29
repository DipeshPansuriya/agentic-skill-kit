# Security Policy

## Supported versions
| Version | Supported |
|---|---|
| 1.x (latest on `main`) | ✅ |
| Older | ❌ |

## Reporting a vulnerability
**Please don't open a public issue for security problems.**

Report privately through GitHub: **Security → Report a vulnerability** on this repository (private vulnerability reporting is enabled).

Please include:
- the affected plugin, skill, hook or script, and its version
- steps to reproduce, or a proof of concept (please don't include real secrets)
- the impact you expect

You can expect an acknowledgement within **5 working days**, and an initial assessment within **10 working days**. Fixes are released as a new version and credited in the release notes, unless you'd prefer not to be named.

## Scope
In scope: anything in this repository, including the skills' instructions, the Python helper scripts, the guard plugin's hooks, and the CI gate.

Out of scope: Claude Code itself (report to Anthropic), and third-party tools the skills mention.

## Design notes for reviewers
- The guard plugin's hooks and all helper scripts run **locally** with the Python standard library. They make **no network calls**.
- The scanners mask secret values in their output and only print the first 4 characters.
- The deliberately vulnerable test samples keep fake credentials as **placeholders**. They're rendered at test time by `render_samples.py`, so the repo never contains secret-shaped strings.
