# Contributing

Thanks for helping improve the kit.

## Workflow
1. Fork the repo, or create a branch: `feat/<skill>-<change>` or `fix/<skill>-<issue>`.
2. Make your change and run the checks locally:
   ```bash
   python .github/scripts/check_repo.py
   ```
3. Open a pull request against `main`. The **validate** workflow must pass before merging, and `main` accepts changes only through pull requests.

## Skill rules
- `name` must be kebab-case and match its folder name.
- `description` must be 250 characters or fewer and include a "Use when the user …" clause.
- Keep `SKILL.md` short (a body under 150 lines is ideal) and put detail in `references/`.
- Every file you add must be referenced from `SKILL.md`.
- Update `evals/test-cases.md`. Every bug fix adds a test case.
- Never commit real or secret-shaped credentials. Test samples use placeholders; see `render_samples.py`.
- Bump the plugin `version` in `.claude-plugin/plugin.json` for any user-facing change.

## Commit messages
Use Conventional Commits, e.g. `feat(sql-performance-tuning): detect key lookups` or `fix(sec_scan): ignore test fixtures`.
