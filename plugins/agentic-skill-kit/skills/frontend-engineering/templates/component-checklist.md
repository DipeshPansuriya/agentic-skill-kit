# Component Checklist

Run before returning any new or changed component. Mark each line ✅ / ❌ / N/A; fix every ❌ or list it under Needs input.

## Structure
- [ ] File paths follow the repo layout (feature folder, naming convention)
- [ ] Framework version stated; only that version's APIs used (no deprecated APIs without a flag)
- [ ] Props/inputs typed; no `any`; required vs optional correct
- [ ] One responsibility per component; data fetching separated from presentation where the repo does so

## State & data
- [ ] State lives in the smallest scope that works (React: local → lifted → Context/Zustand/RTK; Angular: signal → service)
- [ ] Server data via TanStack Query / RTK Query (React) or service + `toSignal`/`switchMap` (Angular), not copied into global stores
- [ ] Stale requests cancelled (AbortSignal / `switchMap`); no race on fast input
- [ ] Subscriptions/effects cleaned up (`useEffect` cleanup / `takeUntilDestroyed`)

## UI states
- [ ] Loading (`role="status"`)
- [ ] Error with retry (`role="alert"`), network vs server vs validation distinguished
- [ ] Empty state with next action
- [ ] Success, including mutation confirmation

## Forms (if any)
- [ ] Visible labels, required marked in text
- [ ] Validation on blur/submit; messages say how to fix; linked with `aria-describedby`
- [ ] Server `errors[]` mapped to fields; input preserved on error
- [ ] Double submit prevented

## Accessibility (WCAG 2.2 AA)
- [ ] Semantic elements; keyboard operable; focus visible and not obscured
- [ ] Contrast ≥ 4.5:1 text, ≥ 3:1 UI; status not by colour alone
- [ ] Targets ≥ 24×24 px; drag has a click alternative
- [ ] Dialogs trap and return focus

## Performance
- [ ] Stable keys / `track` by ID
- [ ] Lists > ~200 rows virtualised
- [ ] Memoisation (React) or OnPush + signals (Angular) where it matters, not everywhere
- [ ] Heavy/rare parts lazy-loaded (`lazy` + `Suspense` / `@defer`, lazy routes)

## Security & i18n
- [ ] No unsanitised HTML, no unsafe URL bindings
- [ ] No tokens in `localStorage`; no secrets in the bundle
- [ ] User-facing strings externalised; dates/numbers via `Intl` or pipes

## Tests
- [ ] Render + main interaction + error or empty state covered
- [ ] Queries by role/label/text; network mocked (MSW / `HttpTestingController`)
- [ ] Run command given
