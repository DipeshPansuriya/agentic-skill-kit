# Ponytail Integration (optional helper for `minimize` mode)

Ponytail is an open-source (MIT) plugin for AI coding agents, by DietrichGebert
(https://github.com/DietrichGebert/ponytail), that pushes the agent toward writing and keeping
only the code a task really needs. It is a plugin/skill inside the agent, **not** a CLI binary:
don't look for it on `PATH` and don't try to `pip`/`npm` install it.

This skill works without it. When present, Ponytail is a second pair of eyes for over-engineering;
it never replaces this skill's safety net.

## 1. Detect
Ponytail is available if any of these appear in the agent's own list of available skills,
slash commands or plugins:
- a skill or plugin named `ponytail`
- commands such as `/ponytail`, `/ponytail-review`, `/ponytail-audit`
Otherwise treat it as missing. Don't guess from files in the user's repo.

## 2. Commands and when this skill uses them
| Command | What it does (in short) | Used in this skill |
|---|---|---|
| `/ponytail [lite\|full\|ultra\|off]` | Sets how hard the agent pushes for minimal code (default `full`) | Step 5, before minimizing |
| `/ponytail-review` | Points out over-engineering in a diff | Step 5, on the refactor diff |
| `/ponytail-audit` | Scans a repo for complexity hotspots | Step 1 (scoping) for repo-wide requests |
| `/ponytail-debt` | Lists shortcuts that were deferred | Risks / follow-ups section |
| `/ponytail-gain` | Reports its own metrics | Optional; our numbers still come from `scripts/code_metrics.py` |
| `/ponytail-help` | Help | - |

Default intensity can also come from the `PONYTAIL_DEFAULT_MODE` environment variable or
`~/.config/ponytail/config.json`. Respect a value the user already set; tell them if you change it
for this session.

## 3. Which intensity
| Situation | Intensity |
|---|---|
| Normal `minimize` request with a working test suite | `full` (default) |
| Good coverage (characterization tests + unit tests on every touched branch) and the user wants maximum reduction | `ultra` |
| Legacy code, weak tests, regulated logic (customs, DG, billing, messaging formats) | `lite` |
| `tidy` / `legacy` modes, or the user wants explicit control | `off`, use this skill's ladder only |

## 4. Flow inside `minimize` mode
1. Safety net ready (Step 2) and "before" metrics captured (Step 3).
2. Set intensity (table above). For a repo-wide ask, run `/ponytail-audit` to pick targets.
3. Make the changes with this skill's minimize ladder; run `/ponytail-review` on the diff.
4. Treat each Ponytail suggestion as a *proposal*: accept it only if it
   - keeps the public API (unless the user asked to change it),
   - keeps validation, error handling, security checks, logging needed for audits, accessibility,
   - is at least as readable for this team,
   - passes the tests and the equivalence check.
5. Re-run `scripts/code_metrics.py --compare` and fill the report. Mention in "Steps applied" which steps came from Ponytail.

Ponytail output goes through the same tests and metrics as any other change. It never bypasses
behaviour preservation, and "fewer lines" never wins over a failing or missing test.

## 5. If it is missing
1. Say so in one line and continue with the fallback (section 6); don't block the refactor.
2. Offer the install commands for the user's agent and **ask before installing**. Never install
   plugins silently. If this environment can't install plugins (sandbox, no plugin support,
   managed settings), just give the commands for the user to run themselves.

| Agent | Install |
|---|---|
| Claude Code | `/plugin marketplace add DietrichGebert/ponytail` then `/plugin install ponytail@ponytail` |
| OpenAI Codex CLI | `codex plugin marketplace add DietrichGebert/ponytail` then `codex plugin add ponytail@ponytail` |
| GitHub Copilot CLI | `copilot plugin marketplace add DietrichGebert/ponytail` then `copilot plugin install ponytail@ponytail` |
| Cursor / Windsurf / Cline | Copy the rule files from the repo's `.cursor/rules` or `.windsurf/rules` folder into the project |

Commands can change between releases; if one fails, point the user to the repo README.

## 6. Fallback: this skill's minimize ladder
Ask in order, stop at the first "yes":
1. **Does it need to exist?** Unused code, speculative options, config nobody sets, layers with one implementation and no test seam need → delete (YAGNI).
2. **Does the repo already have it?** Shared helper, base class, existing util → reuse.
3. **Does the stdlib / framework do it?** `dict.fromkeys`, `ArgumentNullException.ThrowIfNull`, `Collectors`, `COALESCE`, Angular `async` pipe → use it.
4. **Then write the minimal clear code**, using `references/stack-idioms.md`.

Never trade away validation, error handling, security, accessibility or readability for line count.
