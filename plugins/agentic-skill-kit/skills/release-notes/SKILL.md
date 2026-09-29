---
name: release-notes
description: Turn ticket lists, commit messages or a changelog into client-facing and internal release notes (New, Improved, Fixed, Known issues, Breaking). Use when the user asks for release notes, a changelog, what's new, or a deployment note.
---

# Release Notes (Client + Internal)

## Inputs
- Jira/ADO ticket export (key, summary, type, component, status)
- Commit messages (`git log --oneline` or with bodies), PR titles
- Existing CHANGELOG, deployment checklist, known-issue list
- Optional: previous release notes (for tone and numbering)

Several sources: merge by ticket ID. If a ticket and a commit disagree (e.g. ticket "Won't fix" but commit exists), flag it under Needs input and leave it out of the client variant.

## Defaults (ask vs assume)
| Setting | Default if not stated | Options |
|---|---|---|
| Variants | Both: client-facing + internal | Client only · Internal only |
| Version / date | TBD (never guess) | User-supplied |
| Client IDs | Hidden in client variant | Show ticket IDs if user asks |
| Audience name | "Customers" | Specific client/airline/GHA |
| Channel | Document / email | Portal banner (≤ 3 bullets) |

Ask one question only if the version or release date is needed and missing for an external send. Otherwise mark TBD and continue.

## Steps
1. Read all input once. Drop items not released (status not Done/Closed/Deployed) and list them under Needs input.
2. If input is commits, run `python scripts/parse_commits.py FILE` (add `--client` for a first client draft). Use its grouping; move "Unclassified" items into a category by reading them, or list them under Needs input.
3. Classify each item into New · Improved · Fixed · Known issues · Breaking/Action required. Rules in `references/categories-and-tone.md`.
4. Internal variant: keep ticket IDs, components, config changes, DB migrations, feature flags, rollback steps, partner/interface impact (EDI, API versions).
5. Client variant: rewrite each item as a user benefit (who gains what), remove internal IDs, hosts, component names, and internal-only items (refactor, CI, deps) unless they change behaviour.
6. Breaking/Action required: say exactly what the reader must do, by when, and what happens if they do not.
7. Fill `templates/notes-template.md` (both variants). See `templates/example-notes.md` for a filled example (fake data).
8. Run the self-check and fix before returning.

## Format
Use `templates/notes-template.md`. Category order is fixed: Breaking/Action required first, then New, Improved, Fixed, Known issues. Omit nothing: empty category = "None".

## Rules
- **Branding only on request:** use plain, neutral formatting by default. Apply a company or brand design skill (colours, fonts, logo, templates) only when the user names that skill or brand in the request; never pick one automatically.
- Never invent features, dates, versions, IDs, or migration steps. Write TBD and list under Needs input.
- Keep ticket IDs, version numbers, API paths and message types exactly as given.
- Client variant: benefit language ("You can now..."), no internal IDs unless asked, no blame, no security detail beyond "security improvement".
- Internal variant: every Breaking item has migration + rollback notes, or TBD.
- One line per item; ≤ 20 words in client variant.
- A fix of a customer-visible bug appears in both variants; a pure refactor appears only in internal.
- Known issues always include a workaround or "No workaround yet".

## Self-check
- [ ] Every released input item appears in the internal variant (or listed as dropped with reason)
- [ ] Client variant has no ticket IDs, hashes, hosts or component names (unless asked)
- [ ] Every Breaking item states action, deadline, consequence
- [ ] Migration/rollback/config sections filled or TBD
- [ ] Nothing invented; version/date TBD if not given

## Output
Return both variants (client first), then an **Assumptions & Needs input** block: defaults used, unreleased items dropped, unclassified commits, TBDs.

After edits to this skill, rerun `evals/test-cases.md`.
