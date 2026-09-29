# React Reference (React 18/19, TypeScript)

Default: React 19 + TypeScript strict + Vite. If `package.json` shows React 18, avoid 19-only APIs (`use`, `useActionState`, `useOptimistic`, `ref` as a prop, form `action` functions) and say so. Create React App is deprecated: use Vite or a framework (Next.js, React Router framework mode) for new apps.

## Project structure (feature-based)
```
src/
  app/                 providers (QueryClientProvider, Router, theme), App.tsx
  features/bookings/   BookingList.tsx, BookingForm.tsx, api.ts, hooks.ts, types.ts, *.test.tsx
  shared/ui/           Button, Dialog, Table (design-system wrappers)
  shared/lib/          http client, formatters, i18n
  test/setup.ts        @testing-library/jest-dom import, MSW server
```

## Hooks rules & idioms
| Rule | Why |
|---|---|
| Call hooks only at top level of components/custom hooks; never in conditions/loops | Hook order must be stable |
| Keep `useEffect` for syncing with external systems (subscriptions, DOM APIs), not for deriving state or fetching by default | Derived state: compute during render; fetching: TanStack Query / framework loaders |
| Complete dependency arrays (`eslint-plugin-react-hooks`) | Stale closures |
| Cleanup effects (unsubscribe, abort) | StrictMode double-invokes effects in dev to expose missing cleanup |
| Custom hooks start with `use` and return stable shapes | Reuse + testability |
| Stable, unique `key` from data (`id`), never array index for reorderable lists | Wrong state reuse, lost input focus |
| Controlled inputs for validation-heavy forms; React Hook Form + Zod for large forms | Performance + typed schemas |
| React 19: `ref` is a regular prop; `forwardRef` no longer needed (to be deprecated) | Simpler components |
| React 19: `<Context>` as provider; `use(promise/context)`; Actions with `useActionState`, `useFormStatus`, `useOptimistic` | Form/mutation ergonomics |

## State management: choose the smallest thing that works
| Need | Choose |
|---|---|
| UI state for one component | `useState` / `useReducer` |
| Shared by a few nearby components | Lift state up; pass props |
| App-wide, rarely changing (theme, locale, current user) | Context (split contexts; memoise value) |
| Server data (fetch, cache, refetch, pagination, mutations) | **TanStack Query** (or RTK Query if already on Redux) |
| Frequently changing client state shared widely | **Zustand** (small, selector-based) |
| Large app with complex client state, devtools/time-travel, existing Redux | **Redux Toolkit** (`createSlice`, RTK Query); never hand-written Redux boilerplate |
| URL-shareable state (filters, page) | Search params (router) |
Don't copy server data into Redux/Zustand/Context; keep one source of truth.

## Error handling
- Error boundaries (`react-error-boundary`) around routes/widgets; React 19 adds `onCaughtError`/`onUncaughtError` on `createRoot`.
- TanStack Query: `isError` + `error` per query; `throwOnError` to hand to a boundary.
- Parse API problem details (`title`, `detail`, `errors[]`) and map field errors onto the form.

## Testing (React Testing Library)
- Runner: Vitest (Vite) or Jest; `@testing-library/react`, `@testing-library/user-event`, `@testing-library/jest-dom`.
- Query priority: `getByRole` → `getByLabelText` → `getByText` → `getByTestId` last.
- `await userEvent.setup().click(...)`; `findBy*` for async UI; no manual `act()` for RTL-driven updates (import `act` from `react`, not `react-dom/test-utils`, if needed).
- Mock the network, not hooks: MSW (preferred) or `vi.spyOn(globalThis, 'fetch')`. New `QueryClient` per test with `retry: false`.
- Run: `npx vitest` / `npm test`.

## Performance
| Problem | Fix |
|---|---|
| Needless re-renders | Move state down, split components, pass children; `React.memo` + `useMemo`/`useCallback` only where profiling shows benefit. React Compiler (v1.0) auto-memoises if the repo enables it |
| Context re-renders everything | Split contexts; Zustand selectors; memoise provider value |
| Long lists (> ~200 rows) | Virtualise: TanStack Virtual or `react-window` |
| Slow input while filtering | `useDeferredValue` / `useTransition` |
| Big bundles | Route-level `lazy()` + `<Suspense fallback>`; analyse bundle |
| Waterfalls | Fetch in parallel; prefetch with Query; framework loaders |

## Security pitfalls
- `dangerouslySetInnerHTML` with API data → sanitise with DOMPurify or render text.
- `href={userInput}` allows `javascript:` URLs → allow-list `https:`/relative.
- `VITE_*` / `NEXT_PUBLIC_*` env vars are public; never put secrets there.
- Tokens: see `ui-shared.md` (prefer HttpOnly cookies / BFF).

## Deprecated / removed (flag when seen)
`ReactDOM.render`/`hydrate` (removed in 19 → `createRoot`/`hydrateRoot`), `defaultProps` on function components (removed in 19 → default parameters), `propTypes` (ignored in 19 → TypeScript), string refs, legacy context, `react-dom/test-utils`, `componentWillMount`/`componentWillReceiveProps`, Create React App.

## Snippet: TanStack Query list with all states + RTL test
```tsx
// src/features/bookings/BookingList.tsx
import { useQuery } from '@tanstack/react-query';

export type Booking = {
  id: string;
  awbNumber: string;
  pieces: number;
  status: 'BOOKED' | 'DEPARTED' | 'CANCELLED';
};

async function fetchBookings(origin: string, signal: AbortSignal): Promise<Booking[]> {
  const res = await fetch(`/api/v1/bookings?origin=${encodeURIComponent(origin)}`, { signal });
  if (!res.ok) {
    throw new Error(`Could not load bookings (${res.status}).`);
  }
  const body = (await res.json()) as { items: Booking[] };
  return body.items;
}

export function BookingList({ origin }: { origin: string }) {
  const { data, isPending, isError, error, refetch } = useQuery({
    queryKey: ['bookings', origin],
    queryFn: ({ signal }) => fetchBookings(origin, signal),
  });

  if (isPending) return <p role="status">Loading bookings…</p>;

  if (isError) {
    return (
      <div role="alert">
        <p>{error.message}</p>
        <button type="button" onClick={() => void refetch()}>
          Retry
        </button>
      </div>
    );
  }

  if (data.length === 0) return <p>No bookings from {origin}.</p>;

  return (
    <table>
      <caption>Bookings from {origin}</caption>
      <thead>
        <tr>
          <th scope="col">AWB</th>
          <th scope="col">Pieces</th>
          <th scope="col">Status</th>
        </tr>
      </thead>
      <tbody>
        {data.map((b) => (
          <tr key={b.id}>
            <td>{b.awbNumber}</td>
            <td>{b.pieces}</td>
            <td>{b.status}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
```
```tsx
// src/features/bookings/BookingList.test.tsx  (Vitest + RTL; setup file imports '@testing-library/jest-dom/vitest')
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import type { ReactElement } from 'react';
import { afterEach, expect, it, vi } from 'vitest';
import { BookingList } from './BookingList';

function renderWithClient(ui: ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });

afterEach(() => {
  vi.restoreAllMocks();
});

it('renders a row per booking', async () => {
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(
    json({ items: [{ id: '1', awbNumber: '176-12345675', pieces: 2, status: 'BOOKED' }] }),
  );
  renderWithClient(<BookingList origin="BOM" />);

  expect(screen.getByRole('status')).toHaveTextContent('Loading bookings');
  expect(await screen.findByRole('cell', { name: '176-12345675' })).toBeInTheDocument();
});

it('shows the empty state', async () => {
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(json({ items: [] }));
  renderWithClient(<BookingList origin="DXB" />);

  expect(await screen.findByText('No bookings from DXB.')).toBeInTheDocument();
});

it('shows an error and retries', async () => {
  const fetchMock = vi
    .spyOn(globalThis, 'fetch')
    .mockResolvedValueOnce(json({ title: 'Server error' }, 500))
    .mockResolvedValueOnce(json({ items: [{ id: '2', awbNumber: '020-11111111', pieces: 1, status: 'DEPARTED' }] }));
  renderWithClient(<BookingList origin="FRA" />);

  expect(await screen.findByRole('alert')).toHaveTextContent('Could not load bookings (500).');
  await userEvent.setup().click(screen.getByRole('button', { name: 'Retry' }));

  expect(await screen.findByRole('cell', { name: '020-11111111' })).toBeInTheDocument();
  expect(fetchMock).toHaveBeenCalledTimes(2);
});
```
