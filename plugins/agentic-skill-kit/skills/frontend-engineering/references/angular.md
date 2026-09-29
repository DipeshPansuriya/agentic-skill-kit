# Angular Reference (Angular 17+)

Default: Angular 17+ with standalone components, signals, built-in control flow, OnPush, typed reactive forms, `inject()`, functional interceptors/guards. Check `@angular/core` in `package.json`:
| Version | Notes |
|---|---|
| < 17 | NgModules, `*ngIf`/`*ngFor`; match it, flag upgrade path (`ng update` one major at a time) |
| 17–18 | `@if`/`@for`/`@switch`, `@defer`, signal `input()`/`output()` (17.1+/17.3+), `standalone: true` must be written |
| 19+ | `standalone` is the default (omit it); `linkedSignal`, `resource` (experimental) |
| 20+ | `effect`, `linkedSignal`, `toSignal` stable; zoneless stable from 20.2; `*ngIf`/`*ngFor`/`*ngSwitch` deprecated |
| 21+ | New projects zoneless and on Vitest by default; Karma deprecated; Signal Forms experimental |

## Project structure
```
src/app/
  app.config.ts           provideRouter, provideHttpClient(withInterceptors([...])), provideZonelessChangeDetection (if used)
  app.routes.ts           lazy routes: loadComponent / loadChildren
  core/                   interceptors, guards, error handler, auth
  shared/ui/              dumb presentational components
  features/bookings/      booking-search.component.ts, booking.service.ts, booking.routes.ts, *.spec.ts
```
One component per file; kebab-case file names; `app-` selector prefix (or the repo's).

## Idioms & conventions
| Topic | Do | Avoid |
|---|---|---|
| Components | Standalone, `ChangeDetectionStrategy.OnPush`, small templates | New NgModules; default change detection in new code |
| Inputs/outputs | `input()`, `input.required()`, `output()`, `model()` | `@Input()` setters with side effects in new code |
| DI | `inject()` in field initialisers | Constructor param lists in new code (fine to match existing) |
| Local state | `signal`, `computed`; `linkedSignal` for state reset by an input | `BehaviorSubject` for simple component state |
| Side effects | `effect()` only for syncing to non-signal APIs (localStorage, logging, 3rd-party widgets) | Using `effect` to set other signals (use `computed`/`linkedSignal`) |
| Templates | `@if`, `@for (x of xs; track x.id)` with `@empty`, `@switch`, `@defer` | `*ngIf`/`*ngFor` (deprecated v20); `track $index` on mutable lists; function calls in templates (except signals) |
| RxJS ↔ signals | `toSignal(obs$)`, `toObservable(sig)`, `takeUntilDestroyed()` | Manual `subscribe` without teardown |
| HTTP | `provideHttpClient(withInterceptors([fn]))`, functional `HttpInterceptorFn` | `HttpClientModule` (deprecated v18), class interceptors via `HTTP_INTERCEPTORS` in new code |
| Guards/resolvers | Functional `CanActivateFn`, `ResolveFn` | Class-based guards (`CanActivate` interface deprecated) |
| Forms | Typed reactive forms: `FormGroup<{...}>`, `nonNullable: true`, `NonNullableFormBuilder` | `UntypedFormGroup`, template-driven forms for complex validation |
| Global state | Signals in a `providedIn: 'root'` service; NgRx SignalStore or NgRx Store only when the app needs it | NgRx for local component state |

## RxJS best practices
| Case | Operator |
|---|---|
| Search/typeahead, latest wins (cancel previous) | `switchMap` |
| Save queue, order matters | `concatMap` |
| Ignore clicks while busy (submit button) | `exhaustMap` |
| Parallel independent requests | `forkJoin` / `mergeMap` with concurrency |
| Input debouncing | `debounceTime(300)`, `distinctUntilChanged()` |
| Errors inside a long-lived stream | `catchError` **inside** the inner observable so the outer stream survives |
| Teardown | `takeUntilDestroyed()` (injection context) or `async` pipe / `toSignal` |
Avoid nested `subscribe`, `shareReplay` without `{ bufferSize: 1, refCount: true }` for cold HTTP, and `toPromise()` (deprecated → `firstValueFrom`).

## Error handling
- Interceptor maps HTTP errors (401 → re-auth, 5xx → toast/log) and adds correlation IDs; components still handle their own error UI.
- Parse problem details (`title`, `detail`, `errors[]`) and set field errors with `control.setErrors({ server: message })`.
- Global `ErrorHandler` for uncaught errors → log to monitoring.

## Testing
- `TestBed.configureTestingModule({ imports: [StandaloneComponent], providers: [provideHttpClient(), provideHttpClientTesting()] })`.
- `HttpTestingController`: `expectOne`, `flush`, `verify()` in `afterEach`.
- Signal inputs: `fixture.componentRef.setInput('origin', 'BOM')`.
- Query the DOM by role/text (Angular Testing Library is a good option) and assert what the user sees.
- Runner: Vitest (default for new v21+ projects), Jest (`jest-preset-angular`), or Karma/Jasmine (deprecated; fine in existing repos). `expect(...).toContain/toBe` work in all three.
- Run: `ng test` (or `npx jest`).

## Performance pitfalls
- Default change detection + heavy templates → OnPush + signals.
- `@for` without a stable `track` → DOM recreated.
- Long lists → CDK virtual scroll (`cdk-virtual-scroll-viewport`).
- Large initial bundle → lazy routes, `@defer (on viewport)`.
- Multiple subscriptions to the same HTTP observable → one `toSignal` or `shareReplay`.

## Security pitfalls
- Angular escapes interpolation; `[innerHTML]` is sanitised — never bypass with `DomSanitizer.bypassSecurityTrustHtml` for untrusted data.
- Don't build URLs for `[href]`/`[src]` from raw input without validation.
- `HttpClient` XSRF support works only for same-origin cookie auth (`withXsrfConfiguration`).
- Tokens: see `ui-shared.md`; interceptor must only attach tokens to your own API origin.

## Snippet: search with typed form, signals, switchMap, all states + TestBed test
```ts
// src/app/features/bookings/booking.service.ts
import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, map } from 'rxjs';

export interface Booking {
  id: string;
  awbNumber: string;
  pieces: number;
  status: 'BOOKED' | 'DEPARTED' | 'CANCELLED';
}

@Injectable({ providedIn: 'root' })
export class BookingService {
  private readonly http = inject(HttpClient);

  search(origin: string): Observable<Booking[]> {
    const params = new HttpParams().set('origin', origin);
    return this.http.get<{ items: Booking[] }>('/api/v1/bookings', { params }).pipe(map((res) => res.items));
  }
}
```
```ts
// src/app/features/bookings/booking-search.component.ts
import { HttpErrorResponse } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Subject, catchError, of, switchMap, tap } from 'rxjs';
import { Booking, BookingService } from './booking.service';

@Component({
  selector: 'app-booking-search',
  standalone: true, // default from v19; required on v17/18
  imports: [ReactiveFormsModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <form [formGroup]="form" (ngSubmit)="submit()" novalidate>
      <label for="origin">Origin airport (IATA)</label>
      <input
        id="origin"
        formControlName="origin"
        autocomplete="off"
        [attr.aria-invalid]="showOriginError()"
        [attr.aria-describedby]="showOriginError() ? 'origin-error' : null"
      />
      @if (showOriginError()) {
        <p id="origin-error" class="error">
          @if (form.controls.origin.hasError('required')) {
            Origin is required.
          } @else {
            Use a 3-letter IATA code, for example BOM.
          }
        </p>
      }
      <button type="submit" [disabled]="loading()">Search</button>
    </form>

    @if (loading()) {
      <p role="status">Loading bookings…</p>
    } @else if (error()) {
      <p role="alert">{{ error() }}</p>
    } @else if (searched()) {
      <ul aria-label="Bookings">
        @for (b of bookings(); track b.id) {
          <li>{{ b.awbNumber }} · {{ b.pieces }} pcs · {{ b.status }}</li>
        } @empty {
          <li>No bookings found.</li>
        }
      </ul>
    }
  `,
})
export class BookingSearchComponent {
  private readonly bookingService = inject(BookingService);
  private readonly search$ = new Subject<string>();

  readonly form = new FormGroup({
    origin: new FormControl('', {
      nonNullable: true,
      validators: [Validators.required, Validators.pattern(/^[A-Z]{3}$/)],
    }),
  });

  readonly bookings = signal<Booking[]>([]);
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);
  readonly searched = signal(false);

  constructor() {
    this.search$
      .pipe(
        tap(() => {
          this.loading.set(true);
          this.error.set(null);
        }),
        switchMap((origin) =>
          this.bookingService.search(origin).pipe(
            catchError((err: HttpErrorResponse) => {
              this.error.set(
                err.status === 0
                  ? 'Network error. Check your connection and try again.'
                  : `Could not load bookings (${err.status}).`,
              );
              return of(null);
            }),
          ),
        ),
        takeUntilDestroyed(),
      )
      .subscribe((items) => {
        this.loading.set(false);
        if (items) {
          this.bookings.set(items);
          this.searched.set(true);
        }
      });
  }

  showOriginError(): boolean {
    const control = this.form.controls.origin;
    return control.invalid && control.touched;
  }

  submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.search$.next(this.form.controls.origin.value);
  }
}
```
```ts
// src/app/features/bookings/booking-search.component.spec.ts
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { BookingSearchComponent } from './booking-search.component';

describe('BookingSearchComponent', () => {
  let fixture: ComponentFixture<BookingSearchComponent>;
  let http: HttpTestingController;
  let el: HTMLElement;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [BookingSearchComponent],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();

    fixture = TestBed.createComponent(BookingSearchComponent);
    http = TestBed.inject(HttpTestingController);
    el = fixture.nativeElement;
    fixture.detectChanges();
  });

  afterEach(() => http.verify());

  function searchFor(origin: string): void {
    fixture.componentInstance.form.setValue({ origin });
    el.querySelector<HTMLButtonElement>('button[type="submit"]')!.click();
    fixture.detectChanges();
  }

  it('shows a validation message and sends no request when origin is empty', () => {
    searchFor('');
    expect(el.textContent).toContain('Origin is required.');
    http.expectNone((req) => req.url === '/api/v1/bookings');
  });

  it('renders bookings returned by the API', () => {
    searchFor('BOM');
    http
      .expectOne((req) => req.url === '/api/v1/bookings' && req.params.get('origin') === 'BOM')
      .flush({ items: [{ id: '1', awbNumber: '176-12345675', pieces: 2, status: 'BOOKED' }] });
    fixture.detectChanges();
    expect(el.textContent).toContain('176-12345675');
  });

  it('shows the empty state', () => {
    searchFor('DXB');
    http.expectOne((req) => req.url === '/api/v1/bookings').flush({ items: [] });
    fixture.detectChanges();
    expect(el.textContent).toContain('No bookings found.');
  });

  it('shows an error message when the API fails', () => {
    searchFor('FRA');
    http
      .expectOne((req) => req.url === '/api/v1/bookings')
      .flush({ title: 'Server error' }, { status: 500, statusText: 'Server Error' });
    fixture.detectChanges();
    expect(el.querySelector('[role="alert"]')?.textContent).toContain('Could not load bookings (500).');
  });
});
```
