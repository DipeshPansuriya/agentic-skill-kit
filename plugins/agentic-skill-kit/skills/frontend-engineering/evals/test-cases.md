# Test Cases: frontend-engineering

Rerun after every edit. Score with the 5-point checklist (correct framework/version, compiles as written, all UI states + tests, accessibility/security rules applied, usable as-is).

| # | Type | Request | Should trigger? | Expected |
|---|---|---|---|---|
| 1 | Single (React) | "React component to list shipments with filters, using TanStack Query" | Yes | `references/react.md`; loading/error/empty states; `queryKey` includes filters; RTL + Vitest tests by role |
| 2 | Single (React) | "Why does my useEffect run twice and fetch twice?" + code | Yes | Explains StrictMode dev double-invoke; cleanup/AbortController or move fetch to TanStack Query |
| 3 | Single (React) | "Should I use Context, Zustand or Redux Toolkit for the booking wizard?" | Yes | State choice table from `references/react.md`; recommendation with trade-offs; no server data in client store |
| 4 | Single (React) | "This 5,000-row table is slow" + React code | Yes | Virtualisation (TanStack Virtual/react-window), stable keys, targeted memo; not blanket `useMemo` |
| 5 | Single (Angular) | "Angular 18 standalone component for flight search with a typed reactive form" | Yes | `references/angular.md`; `standalone: true`, OnPush, `@if`/`@for` with `track`, typed `FormGroup`, TestBed + `HttpTestingController` |
| 6 | Single (Angular) | "Add an auth interceptor that attaches the token" | Yes | Functional `HttpInterceptorFn` + `withInterceptors`; attaches only to own API origin; token storage advice from `references/ui-shared.md` |
| 7 | Single (Angular) | "My typeahead shows old results sometimes" + RxJS code with `mergeMap` | Yes | Diagnoses race; `debounceTime` + `distinctUntilChanged` + `switchMap`; `catchError` inside inner stream |
| 8 | Accessibility | "Make this booking form accessible" + JSX | Yes | WCAG 2.2 AA checklist; labels, `aria-describedby`, error summary, target size, focus |
| 9 | Multi-stack | "Angular UI + .NET API to create a booking" | Yes | Angular side here; API handed to backend-engineering; one DTO + problem-details contract; server errors mapped to form fields |
| 10 | Edge: unknown version | "Write an Angular component for AWB tracking" (no package.json) | Yes | States assumed Angular 17+; notes `standalone` default from v19; control flow syntax |
| 11 | Edge: legacy code | Angular 14 NgModule code with `*ngIf` and `HttpClientModule` | Yes | Fix stays in NgModule style; flags `*ngIf` (deprecated v20) and `HttpClientModule`; upgrade path separate |
| 12 | Edge: legacy React | React 17 class component with `componentWillReceiveProps` | Yes | Matches React 17 APIs or asks; flags unsafe lifecycle; offers hook-based rewrite separately |
| 13 | Edge: unsafe request | "Store the JWT in localStorage so it survives refresh" | Yes | Explains XSS risk; proposes HttpOnly cookie/BFF or in-memory + refresh; implements safe option |
| 14 | Near-miss | "Tune this SQL query for the bookings grid" | **No** (sql-performance-tuning) | |
| 15 | Near-miss | "Review this PR" + frontend diff | **No** (code-review) | |
| 16 | Near-miss | "Micro-frontends or a monorepo SPA for the cargo portal?" | **No** (software-architecture) | |
| 17 | Near-miss | "Design a branded login screen mock-up" | **No** (visual design, not code) | |
| 18 | Consistency | Run #1 ×3 | Yes | Same output sections (Assumptions → Plan → Code → Tests → Decisions → Needs input) 3/3 |
