# Frontend Performance (React · Angular · Web Vitals)

## Goal metrics (Core Web Vitals, 75th percentile of real users)
| Metric | Good | Needs improvement | Poor | Usual causes |
|---|---|---|---|---|
| **LCP** Largest Contentful Paint | ≤ 2.5 s | ≤ 4.0 s | > 4.0 s | Slow TTFB, render-blocking JS/CSS, unoptimized hero image, client-only rendering |
| **INP** Interaction to Next Paint (replaced FID in March 2024) | ≤ 200 ms | ≤ 500 ms | > 500 ms | Long tasks (> 50 ms), heavy re-renders, sync work in handlers |
| **CLS** Cumulative Layout Shift | ≤ 0.1 | ≤ 0.25 | > 0.25 | Images/ads without size, late fonts, injected banners |

## Measure first
| Question | Tool |
|---|---|
| Field data (real users) | `web-vitals` library → analytics / RUM; CrUX / PageSpeed Insights |
| Lab trace: long tasks, layout, scripting | Chrome DevTools Performance panel (CPU 4× throttle), Lighthouse |
| Why did a React component render? | React DevTools Profiler ("Highlight updates", "Why did this render?"), `<Profiler onRender>` |
| Angular change detection cost | Angular DevTools Profiler (change detection cycles per component) |
| Bundle composition | `source-map-explorer`, `webpack-bundle-analyzer`, `rollup-plugin-visualizer` (Vite), `ng build --stats-json` + esbuild analyzer |
| Budget in CI | Angular `budgets` in `angular.json`; Lighthouse CI; `size-limit` |

## React
| Symptom (measured) | Fix | Caveat |
|---|---|---|
| Child re-renders with same props | `React.memo(Child)` | Only helps if props are referentially stable |
| Unstable props (inline objects/functions) break memo | `useMemo` / `useCallback` for those props | Don't wrap everything: memo has a cost; React Compiler (React 19) automates this where enabled |
| Expensive derived value recalculated every render | `useMemo(() => compute(items), [items])` | Only if profiler shows it |
| Long lists (> ~200 rows) | Virtualize: `@tanstack/react-virtual`, `react-window` | Keep stable `key` (id, not index) |
| Big initial bundle | Route-level `React.lazy(() => import('./Page'))` + `<Suspense>`; dynamic `import()` for heavy libs | Check tree-shaking (ESM imports, `import { x } from 'lib'`) |
| Typing lags while list filters | `useDeferredValue` / `startTransition` | Keeps input responsive (INP) |
| Context update re-renders the whole tree | Split contexts, select state with a store (Zustand/Redux selectors) | |
| Request waterfalls | Fetch in parallel, route loaders, React Query/SWR caching, prefetch | Also server-side: SSR/RSC for LCP |
| Effects firing fetch on every render | Correct dependency arrays; derive state instead of syncing | |

## Angular (17+)
| Symptom (measured) | Fix | Notes |
|---|---|---|
| Change detection runs for whole tree | `ChangeDetectionStrategy.OnPush` + immutable inputs / signals | Default for new components |
| Fine-grained updates | Signals (`signal`, `computed`, `input()`) and `async` pipe / `toSignal` | Avoid manual `subscribe` + `detectChanges` |
| Lists re-create DOM | `@for (item of items; track item.id)` (required `track`) or `*ngFor` with `trackBy` | `track $index` only for static lists |
| Function calls in templates recalculate each CD | `computed()` signal or pure pipe | |
| Heavy below-the-fold components | `@defer (on viewport) { ... } @placeholder { ... }` | Splits the chunk automatically |
| Zone.js overhead | Zoneless: `provideExperimentalZonelessChangeDetection()` (v18-19) / `provideZonelessChangeDetection()` (v20+) | Requires signals/OnPush-friendly code; test thoroughly |
| Big initial bundle | Lazy routes (`loadComponent` / `loadChildren`), standalone components, budgets | |
| Event handlers trigger CD on scroll/mousemove | `runOutsideAngular` or throttle; `NgZone`-free with zoneless | |
| Images | `NgOptimizedImage` (`ngSrc`, `priority` on LCP image, width/height) | Fixes LCP + CLS |

## Cross-framework LCP / CLS checklist
| Item | Fix |
|---|---|
| Hero image | Correct size, AVIF/WebP, `fetchpriority="high"`, not lazy-loaded, preload if discovered late |
| Fonts | `font-display: swap` / `optional`, preload critical font, size-adjust fallback |
| Layout shifts | `width`/`height` or `aspect-ratio` on media; reserve space for async content |
| Third-party scripts | `defer`/`async`, load after interaction, audit tag managers |
| Compression / caching | Brotli, immutable hashed assets, CDN, HTTP/2+ |
