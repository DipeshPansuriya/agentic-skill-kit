# agentic-skill-kit-guard

These safety hooks for Claude Code are optional, local only, and make no network calls.

| Event | Check | Result |
|---|---|---|
| After `Write` / `Edit` / `MultiEdit` | Security scan of the edited file (secrets, SQL injection, unsafe deserialization, TLS/CORS…). `.sql` files also get a SQL lint (UPDATE/DELETE without WHERE…) | HIGH/CRITICAL findings go back to Claude to fix |
| Before a `Bash` command that runs `git commit` | Secret scan of staged files | Commit blocked if likely secrets are found |

- To silence a line you've reviewed, add `nosec` to it.
- The hooks never break a session: an internal error exits silently.
- Requires Python 3.
