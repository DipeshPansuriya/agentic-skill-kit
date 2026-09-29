# UI Shared Reference (React and Angular)

## Accessibility: WCAG 2.2 AA checklist
| Area | Check | WCAG |
|---|---|---|
| Semantics | Native elements first (`button`, `a href`, `table`, `label`); headings in order; one `h1` per page; landmarks (`header`, `nav`, `main`) | 1.3.1, 2.4.6 |
| Names | Every input has a visible `<label for>`; icon-only buttons have `aria-label`; images have `alt` (empty `alt=""` if decorative) | 1.1.1, 3.3.2, 4.1.2 |
| Keyboard | Everything operable by keyboard; no traps; logical tab order; no positive `tabindex` | 2.1.1, 2.1.2, 2.4.3 |
| Focus visible | Visible focus ring (don't remove `outline` without replacement); focused element not hidden behind sticky headers/footers | 2.4.7, **2.4.11 (new)** |
| Dialogs | Move focus into dialog, trap while open, `Esc` closes, return focus to trigger (native `<dialog>` or CDK/Radix/Headless UI) | 2.4.3 |
| Colour | Text contrast ≥ 4.5:1 (≥ 3:1 large text); UI components/focus indicators ≥ 3:1; never colour alone for status (add text/icon) | 1.4.3, 1.4.11, 1.4.1 |
| Targets | Pointer targets ≥ 24×24 CSS px or enough spacing | **2.5.8 (new)** |
| Dragging | Any drag action (reorder ULDs, kanban) has a single-pointer alternative (buttons/menus) | **2.5.7 (new)** |
| Forms | Errors identified in text and linked (`aria-describedby`), suggestions given; don't ask users to re-enter data already given in the same flow | 3.3.1, 3.3.3, **3.3.7 (new)** |
| Auth | Login doesn't require cognitive tests (allow paste and password managers) | **3.3.8 (new)** |
| Help | Help/contact links appear in the same place across pages | **3.2.6 (new)** |
| Dynamic content | Async results/errors announced: `role="status"` (polite) / `role="alert"` (assertive) | 4.1.3 |
| Zoom & reflow | Works at 200% zoom and 320 px width without horizontal scroll (except data tables) | 1.4.4, 1.4.10 |
| Motion | Respect `prefers-reduced-motion` | 2.3.3 (AAA, recommended) |
Tools: axe DevTools / `@axe-core/playwright` / `jest-axe` or `vitest-axe`, Lighthouse, keyboard-only walk-through, a screen reader (NVDA, VoiceOver).

## Forms & validation UX
- Label above field; hint text before input; mark required fields (text, not only `*`).
- Validate on blur and on submit, not on every keystroke (except live format hints).
- On submit with errors: show an error summary at the top, focus it, link each item to its field.
- Error text says how to fix: "Use a 3-letter IATA code, for example BOM", not "Invalid".
- Keep user input on error; never clear the form.
- Disable submit only while submitting (prevent double submit); show progress.
- Map server problem details `errors[]` to fields; show `detail` for non-field errors.
- Use correct input types/`inputmode` and `autocomplete` tokens.

## API states: always design all four
| State | Show | Notes |
|---|---|---|
| Loading | Skeleton or spinner with `role="status"` text | Delay spinner ~200 ms to avoid flicker; keep previous data while refetching |
| Error | Plain message + Retry; `role="alert"` | Distinguish network (status 0), 4xx (user can fix), 5xx (try later); show correlation ID for support |
| Empty | Friendly message + next action ("Create booking") | Different from "no results for filter X" → offer "Clear filters" |
| Success | Data; confirmation for mutations (toast + focus management) | Optimistic updates must roll back on error |
| 401 / 403 | Re-authenticate / "You don't have access" | Never show blank screens |

## i18n & localisation
- No hard-coded user-facing strings in new components; use the repo's library: React `react-i18next` / `FormatJS (react-intl)`; Angular `@angular/localize` (build-time) or Transloco (runtime).
- ICU messages for plurals/gender: `{count, plural, one {# piece} other {# pieces}}`.
- Format with `Intl.DateTimeFormat` / `Intl.NumberFormat` (Angular pipes `date`, `number`, `currency`); store/transfer UTC ISO 8601, display in user or station time zone (state which).
- Allow text expansion (+30–40%); avoid fixed widths; support RTL with logical CSS properties (`margin-inline-start`).
- Set `lang` on `<html>`.

## Security
### XSS
- Render untrusted data as text (default in React and Angular). Avoid `dangerouslySetInnerHTML`, `[innerHTML]` with bypass, `eval`, `new Function`, inline event strings.
- If HTML is required (rich text), sanitise with DOMPurify (React) or Angular's built-in sanitiser; never `bypassSecurityTrust*` on user data.
- Validate URLs (`https:` / relative only) before binding to `href`/`src`.

### Token storage
| Option | Verdict |
|---|---|
| HttpOnly, `Secure`, `SameSite=Lax/Strict` cookie set by the server / BFF (backend-for-frontend) | **Preferred.** Not readable by JS; add CSRF protection for cookie auth |
| Access token in memory (JS variable), refresh via HttpOnly cookie | Good for SPAs calling APIs directly; lost on reload → silent refresh |
| `localStorage` / `sessionStorage` | Avoid for tokens: any XSS can read them |
- Use OAuth 2.0 Authorization Code + PKCE (e.g. MSAL, oidc-client-ts, angular-auth-oidc-client); never implicit flow.
- Attach tokens only to your own API origins (interceptor allow-list).
- Log out = clear memory + server session; don't rely on hiding UI for authorisation.

### Content Security Policy (CSP)
- Start with: `default-src 'self'; script-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; connect-src 'self' https://api.example.com`.
- No `'unsafe-inline'`/`'unsafe-eval'` for scripts; use nonces or hashes. Angular supports nonces via `ngCspNonce` / `CSP_NONCE`; Vite/Next.js have nonce support.
- Add `Trusted Types` (`require-trusted-types-for 'script'`) where supported.
- Deploy in `Content-Security-Policy-Report-Only` first; fix violations; then enforce.
- Other headers: `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`, HSTS.

### Other
- Nothing secret in the bundle (`VITE_*`, `NEXT_PUBLIC_*`, Angular `environment.ts` are public).
- Keep dependencies patched (`npm audit`, Dependabot/Renovate); pin lock files.
