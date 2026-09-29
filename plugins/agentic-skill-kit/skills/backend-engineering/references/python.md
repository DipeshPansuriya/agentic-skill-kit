# Python Reference (3.12+, FastAPI / Django, Pydantic v2)

Default: Python 3.12, FastAPI + Pydantic v2, pytest, uv. If `requires-python` shows 3.13/3.14, use their features and say so. If the code uses Pydantic v1 APIs or Python < 3.10, match it and flag the upgrade.

## Project structure
```
pyproject.toml            [project] metadata, deps, [tool.ruff], [tool.pytest.ini_options], [tool.mypy]
uv.lock                   committed lock file (uv) — or requirements*.txt pinned with hashes (pip-tools)
src/cargo_api/
  main.py                 FastAPI app, exception handlers, lifespan
  settings.py             pydantic-settings BaseSettings
  bookings/api.py         router, request/response models
  bookings/service.py     business rules (no FastAPI imports)
  bookings/repository.py  DB access (SQLAlchemy 2.0 async / asyncpg)
tests/                    pytest; conftest.py fixtures
```
Django: `manage.py`, one app per bounded area (`bookings/models.py`, `serializers.py`, `views.py`, `urls.py`), `settings/base.py|prod.py`; DRF for APIs; `pytest-django`.

## Idioms & conventions
| Topic | Do | Avoid |
|---|---|---|
| Typing | Full hints; `list[str]`, `X \| None`, `Annotated`, `type` aliases (3.12); check with mypy or pyright | Untyped public functions, `Any` everywhere |
| Models | Pydantic v2: `model_config = ConfigDict(...)`, `Field(...)`, `@field_validator`, `model_dump()` | v1: `class Config`, `@validator`, `.dict()`, `orm_mode` (use `from_attributes`) |
| FastAPI DI | `Annotated[Repo, Depends(get_repo)]` | Globals imported directly into handlers (untestable) |
| Startup | `lifespan` context manager | `@app.on_event("startup")` (deprecated) |
| Async | `async def` only if everything inside is non-blocking; `asyncio.TaskGroup` (3.11+); `asyncio.timeout()` | `requests`/blocking DB drivers inside `async def` (blocks the event loop) — use `httpx.AsyncClient`, or plain `def` handlers |
| Time | `datetime.now(UTC)` | `datetime.utcnow()` (deprecated 3.12) |
| Lint/format | `ruff check` + `ruff format` | Mixing black/isort/flake8 configs with ruff |
| Django ORM | `select_related` / `prefetch_related`, `F()`/`Q()`, migrations | Queries in loops; raw SQL with f-strings |

## Error handling
- FastAPI returns `{"detail": ...}` by default; register handlers for `StarletteHTTPException` and `RequestValidationError` to return RFC 9457 `application/problem+json` (see snippet).
- Raise domain exceptions in services; translate to HTTP in one handler.
- Catch specific exceptions; never bare `except:`; re-raise with `raise ... from exc`.
- Django/DRF: custom `EXCEPTION_HANDLER` producing problem details; `DEBUG=False` in prod.

## Logging
- `logging.getLogger(__name__)`; configure once with `logging.config.dictConfig`.
- Structured JSON: `structlog` or `python-json-logger`; pass fields via `extra={...}` or structlog kwargs.
- Correlation ID: middleware (e.g. `asgi-correlation-id`) storing the ID in a `contextvars.ContextVar`, added to every record by a `logging.Filter`; OpenTelemetry for traces.
- Use lazy formatting `logger.info("x=%s", x)` with stdlib, never f-strings in hot paths.

## Config & secrets
- `pydantic-settings` `BaseSettings` reading env vars / `.env` (dev only, git-ignored); `SecretStr` for passwords.
- Prod secrets from the platform (Kubernetes secrets, AWS/Azure secret stores, Vault).

## Testing
- pytest + fixtures in `conftest.py`; `pytest.mark.parametrize` for input tables.
- FastAPI: `TestClient` (needs `httpx`; recent Starlette 1.x warns and prefers `httpx2` — install whichever the installed Starlette asks for) with `app.dependency_overrides`; async tests via `pytest-asyncio` or `anyio` + `httpx.AsyncClient(transport=ASGITransport(app))`.
- DB: Testcontainers for Python or a disposable Postgres; avoid SQLite when prod is Postgres.
- Mocks: `unittest.mock` / `pytest-mock`; `respx` for httpx.
- Run: `uv run pytest` (or `python -m pytest`).

## Packaging
- New project: `uv init`, `uv add fastapi uvicorn`, `uv add --dev pytest httpx ruff mypy`, `uv run ...`.
- pip: `python -m venv .venv`, `pip install -e .[dev]` with dependencies declared in `pyproject.toml` (PEP 621); don't rely on `setup.py` for new code.

## Performance pitfalls
- Blocking I/O or CPU-heavy work in `async def` → offload with `asyncio.to_thread` / worker process.
- N+1 queries (SQLAlchemy: `selectinload`; Django: `prefetch_related`).
- Creating a new `httpx`/DB client per request instead of one per app (lifespan).
- Loading full tables into memory; paginate or stream.

## Security pitfalls
- SQL via f-strings → bound parameters (`text("... WHERE id = :id")`, ORM filters, `cursor.execute(sql, params)`).
- `pickle`/`yaml.load` on untrusted data → `json`, `yaml.safe_load`.
- `subprocess(..., shell=True)` with user input; `eval`/`exec`.
- Mass assignment: `extra="forbid"` on input models; separate input and output models.
- Django: keep `SECRET_KEY` out of code, `ALLOWED_HOSTS` set, CSRF middleware on.

## Snippet: FastAPI router + problem details + pytest
```python
# src/cargo_api/bookings/api.py
import logging
from decimal import Decimal
from typing import Annotated, Protocol
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class CreateBooking(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    awb_number: str = Field(pattern=r"^\d{3}-\d{8}$", examples=["176-12345675"])
    pieces: int = Field(ge=1, le=9999)
    weight_kg: Decimal = Field(gt=0, max_digits=10, decimal_places=2)


class Booking(BaseModel):
    id: UUID
    awb_number: str
    pieces: int
    weight_kg: Decimal


class BookingRepository(Protocol):
    async def get(self, booking_id: UUID) -> Booking | None: ...
    async def add(self, booking: Booking) -> None: ...


class InMemoryBookingRepository:
    def __init__(self) -> None:
        self._items: dict[UUID, Booking] = {}

    async def get(self, booking_id: UUID) -> Booking | None:
        return self._items.get(booking_id)

    async def add(self, booking: Booking) -> None:
        self._items[booking.id] = booking


_repository = InMemoryBookingRepository()


def get_repository() -> BookingRepository:
    return _repository


Repo = Annotated[BookingRepository, Depends(get_repository)]
router = APIRouter(prefix="/api/v1/bookings", tags=["bookings"])


@router.get("/{booking_id}")
async def get_booking(booking_id: UUID, repo: Repo) -> Booking:
    booking = await repo.get(booking_id)
    if booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Booking {booking_id} not found")
    return booking


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_booking(payload: CreateBooking, repo: Repo, response: Response) -> Booking:
    booking = Booking(id=uuid4(), **payload.model_dump())
    await repo.add(booking)
    response.headers["Location"] = f"/api/v1/bookings/{booking.id}"
    logger.info("booking_created", extra={"booking_id": str(booking.id), "awb": booking.awb_number})
    return booking
```
```python
# src/cargo_api/main.py
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from cargo_api.bookings.api import router as bookings_router

app = FastAPI(title="Cargo API", version="1.0.0")
app.include_router(bookings_router)


def problem(request: Request, status_code: int, title: str, detail: str, **extra: Any) -> JSONResponse:
    body = {"type": "about:blank", "title": title, "status": status_code,
            "detail": detail, "instance": request.url.path, **extra}
    return JSONResponse(status_code=status_code, content=body, media_type="application/problem+json")


@app.exception_handler(StarletteHTTPException)
async def http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return problem(request, exc.status_code, HTTPStatus(exc.status_code).phrase, str(exc.detail))


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = [{"field": ".".join(str(p) for p in e["loc"][1:]), "message": e["msg"]} for e in exc.errors()]
    return problem(request, 422, "Validation failed", "One or more fields are invalid.", errors=errors)
```
```python
# tests/test_bookings.py
from collections.abc import Iterator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from cargo_api.bookings.api import InMemoryBookingRepository, get_repository
from cargo_api.main import app


@pytest.fixture
def client() -> Iterator[TestClient]:
    repo = InMemoryBookingRepository()
    app.dependency_overrides[get_repository] = lambda: repo
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_create_booking_returns_201_and_location(client: TestClient) -> None:
    resp = client.post("/api/v1/bookings", json={"awb_number": "176-12345675", "pieces": 2, "weight_kg": "12.50"})
    assert resp.status_code == 201
    assert resp.headers["Location"].endswith(resp.json()["id"])


@pytest.mark.parametrize("awb", ["bad", "17612345675", ""])
def test_invalid_awb_returns_problem_details(client: TestClient, awb: str) -> None:
    resp = client.post("/api/v1/bookings", json={"awb_number": awb, "pieces": 1, "weight_kg": "1"})
    assert resp.status_code == 422
    assert resp.headers["content-type"].startswith("application/problem+json")
    assert resp.json()["errors"][0]["field"] == "awb_number"


def test_unknown_booking_returns_404(client: TestClient) -> None:
    resp = client.get(f"/api/v1/bookings/{uuid4()}")
    assert resp.status_code == 404
    assert resp.json()["title"] == "Not Found"
```
Note: Pydantic v2 serialises `Decimal` as a JSON string (`"12.50"`); say so in the API contract.
