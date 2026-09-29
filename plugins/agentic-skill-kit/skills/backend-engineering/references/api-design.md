# API Design Reference (shared by all stacks)

## REST conventions
| Rule | Example |
|---|---|
| Plural nouns, no verbs in paths | `GET /api/v1/bookings/{id}`, not `/getBooking` |
| Sub-resources for ownership | `GET /api/v1/flights/{flightId}/bookings` |
| Actions that aren't CRUD: sub-resource noun | `POST /api/v1/bookings/{id}/cancellation` |
| JSON field casing: pick one, keep it | camelCase (JS clients) or snake_case (Python-first); match existing APIs |
| Dates | ISO 8601 UTC with offset: `2026-09-27T08:30:00Z`; dates only: `2026-09-27` |
| Money / weight | Decimal as string or integer minor units; state unit (`weightKg`) |
| IDs | Opaque strings/UUIDs; never expose sequential DB IDs when enumeration matters |

### Methods & status codes
| Method | Success | Common errors |
|---|---|---|
| `GET` item | 200 | 404 |
| `GET` collection | 200 (empty list, not 404) | 400 bad filter |
| `POST` create | 201 + `Location` header + body | 400/422 validation, 409 duplicate |
| `PUT` replace | 200 or 204 | 404, 409, 412 (ETag mismatch) |
| `PATCH` partial (`application/merge-patch+json`) | 200 | 404, 409, 422 |
| `DELETE` | 204 (also 204 if already gone, for idempotency, or 404: choose and document) | 409 if blocked |
| Async job | 202 + `Location` of status resource | |
| Auth | — | 401 not authenticated, 403 not allowed |
| Throttling | — | 429 + `Retry-After` |

## Versioning
- Default: URL major version `/api/v1/...`. Header/media-type versioning only if the platform already uses it.
- Additive changes (new optional fields, new endpoints) don't need a new version. Clients must ignore unknown fields.
- Breaking changes (remove/rename field, change type or meaning, new required input) → `v2`; run both; announce with `Deprecation` and `Sunset` (RFC 8594) headers.
- Libraries: .NET `Asp.Versioning.Http`; Spring: path prefix per controller (Spring Framework 7 adds built-in API versioning); FastAPI: one `APIRouter` per version.

## Pagination
| Style | Use when | Request / response |
|---|---|---|
| **Cursor / keyset** (default for large or live data) | Feeds, shipments, events; stable under inserts | `?limit=50&cursor=eyJpZCI6...` → `{ "items": [...], "nextCursor": "..." }` |
| Offset | Small, admin-style tables needing page numbers | `?page=2&pageSize=50` → `{ "items": [...], "page": 2, "pageSize": 50, "totalCount": 1234 }` |
- Enforce a max page size (e.g. 100); default 20–50.
- Cursor = opaque, encoded last sort key(s) + direction; always sort by a unique tiebreaker (e.g. `createdAt, id`).
- `totalCount` is expensive on big tables; make it optional.
- Filtering: `?status=DEPARTED&origin=BOM`; sorting: `?sort=-createdAt,awb`.

## Error model: RFC 9457 Problem Details
Content type `application/problem+json` (RFC 9457 obsoletes RFC 7807).
```json
{
  "type": "https://api.example.com/problems/validation-error",
  "title": "Validation failed",
  "status": 422,
  "detail": "One or more fields are invalid.",
  "instance": "/api/v1/bookings",
  "traceId": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
  "errors": [{ "field": "awbNumber", "message": "AWB must look like 176-12345675" }]
}
```
- `type` is a stable URI per error kind (or `about:blank`); `title` doesn't change per occurrence; `detail` is human-readable for this occurrence.
- Extensions allowed: `traceId`/`correlationId`, `errors[]`. Same shape for every endpoint and every stack.
- Never include stack traces, SQL, internal hostnames.
- 400 vs 422: choose one for validation and keep it consistent (ASP.NET Core and Spring default to 400; FastAPI defaults to 422).

## Idempotency keys
- For non-idempotent `POST`s with side effects (bookings, payments, messages to airlines/customs): accept `Idempotency-Key: <uuid>` header (IETF draft `draft-ietf-httpapi-idempotency-key-header`).
- Server stores key + request hash + response (status and body) for a TTL (e.g. 24 h), scoped per client.
  - Same key + same payload → replay stored response.
  - Same key + different payload → 422 (or 409) problem.
  - Same key still processing → 409 with `Retry-After`.
- Store atomically (unique constraint on `(clientId, key)`) in the same transaction as the side effect, or use an outbox.
- `PUT`/`DELETE` are idempotent by design; `GET` must be safe.

## Concurrency
- Optimistic locking: return `ETag` (row version); require `If-Match` on `PUT`/`PATCH`; 412 on mismatch.
- EF Core `[Timestamp]`/`IsRowVersion`, JPA `@Version`, SQLAlchemy `version_id_col`.

## OpenAPI
- OpenAPI 3.1 (3.0 if tooling requires). Generate from code and commit the spec, or design-first and generate servers/clients; choose one.
  - .NET 9+: `Microsoft.AspNetCore.OpenApi` (`AddOpenApi()`); .NET 8: Swashbuckle or NSwag.
  - Spring: `springdoc-openapi-starter-webmvc-ui`.
  - FastAPI: built in (`/openapi.json`, `/docs`).
- Every operation: `operationId`, summary, request/response schemas, all error responses (`4xx` → problem schema), examples, security scheme.
- Lint with Spectral in CI; diff specs (e.g. `oasdiff`) to catch breaking changes.

## Checklist
- [ ] Nouns, correct methods and status codes, `Location` on 201
- [ ] Versioned path; change is additive or a new version
- [ ] Collections paginated with max page size
- [ ] Errors are problem details with correlation/trace ID
- [ ] Side-effecting POST supports `Idempotency-Key`
- [ ] Auth scheme and 401/403 documented in OpenAPI
