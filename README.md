# fastapi-task-manager

Production-ready REST API for task management built with FastAPI, PostgreSQL, and async SQLAlchemy. Demonstrates clean architecture, JWT authentication with refresh tokens, Alembic migrations, and comprehensive test coverage.

**Live API:** https://fastapi-task-manager.onrender.com/docs  
**Repo:** https://github.com/PabloAMoreno97/fastapi-task-manager

---

## What it demonstrates

- **Clean Architecture** — strict separation between routers → services → repositories
- **JWT auth** — access tokens (30 min) + refresh tokens (7 days) stored in DB, revocable on use
- **Async SQLAlchemy 2** — fully async ORM with `asyncpg` driver
- **Alembic migrations** — async-compatible env.py, versioned schema changes
- **Rate limiting** — login endpoint capped at 10 req/min with `slowapi`
- **Structured logging** — JSON-formatted logs
- **Task isolation** — users can only see and modify their own tasks
- **PATCH semantics** — partial updates via `exclude_unset` (only sent fields are changed)
- **Test suite** — 22 tests across unit (security functions) and integration (auth + tasks)

---

## Architecture

```
HTTP Request
    │
    ▼
Router (FastAPI)         ← validates input, returns HTTP response
    │
    ▼
Service                  ← business logic, raises HTTPException on violations
    │
    ▼
Repository               ← data access only, no business logic
    │
    ▼
SQLAlchemy (async)
    │
    ▼
PostgreSQL (Neon in prod / Docker in dev)
```

**Auth flow:**
```
POST /auth/register  →  create user (bcrypt password)
POST /auth/login     →  access_token (30m) + refresh_token (7d, stored in DB)
POST /auth/refresh   →  new access_token, old refresh_token revoked (rotation)
```

---

## Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/register` | — | Create a new user |
| POST | `/auth/login` | — | Get JWT tokens (rate limited: 10/min) |
| POST | `/auth/refresh` | — | Rotate refresh token → new access token |
| GET | `/tasks` | ✓ | List tasks (filter by status/priority, paginated) |
| POST | `/tasks` | ✓ | Create a task |
| GET | `/tasks/{id}` | ✓ | Get a single task |
| PATCH | `/tasks/{id}` | ✓ | Partially update a task |
| DELETE | `/tasks/{id}` | ✓ | Delete a task |
| GET | `/health` | — | Health check |

---

## Quick start (Docker)

The simplest way to run everything. No local PostgreSQL or `.env` file required.

```bash
docker compose up --build
```

API available at http://localhost:8000 — interactive docs at http://localhost:8000/docs

> All database credentials are pre-configured in `docker-compose.yml` for local use.
> On first start, Docker Compose waits for PostgreSQL to be healthy, then runs
> `alembic upgrade head` automatically before starting the API.

---

## Run locally (API only, DB in Docker)

The recommended local dev setup: PostgreSQL runs in Docker, the API runs locally with hot reload.

**Requirements:** Python 3.11+, Docker

```bash
# 1. Install dependencies
pip install -r requirements-dev.txt

# 2. Copy and configure environment
cp .env.example .env
# .env.example defaults (localhost / taskmanager / taskmanager) work as-is for Docker DB

# 3. Start only the PostgreSQL container
docker compose up postgres -d
# Wait ~5 seconds for it to be ready

# 4. Apply migrations
alembic upgrade head

# 5. Start the API with hot reload
uvicorn src.api.main:app --reload
```

API available at http://localhost:8000/docs

To stop the database container when done:
```bash
docker compose down
```

---

## Run locally (API + local PostgreSQL)

If you have PostgreSQL installed locally, skip Docker and create the DB manually.

**Requirements:** Python 3.11+, PostgreSQL 15+

```bash
# 1. Create the database and user
psql -U postgres -c "CREATE USER taskmanager WITH PASSWORD 'taskmanager';"
psql -U postgres -c "CREATE DATABASE taskmanager_db OWNER taskmanager;"

# 2. Install dependencies
pip install -r requirements-dev.txt

# 3. Configure environment
cp .env.example .env
# Edit .env if your PostgreSQL credentials differ from the defaults

# 4. Apply migrations
alembic upgrade head

# 5. Start the API
uvicorn src.api.main:app --reload
```

---

## Run tests

Tests use **SQLite in-memory** — no PostgreSQL or Docker needed.

```bash
pip install -r requirements-dev.txt
pytest -v
```

Expected output: **27 tests passing**

```
tests/unit/test_security.py          (8 tests)  — password hashing, JWT creation/decode
tests/integration/test_auth.py       (9 tests)  — register, login, refresh, error cases
tests/integration/test_tasks.py     (10 tests)  — CRUD, filters, pagination, isolation
```

---

## Project structure

```
fastapi-task-manager/
├── src/
│   ├── api/
│   │   ├── main.py                  # FastAPI app, CORS, rate limiter middleware
│   │   ├── dependencies.py          # DB session, current user extraction
│   │   └── routers/
│   │       ├── auth.py              # /auth/register, /auth/login, /auth/refresh
│   │       ├── tasks.py             # CRUD /tasks
│   │       └── health.py            # /health
│   ├── core/
│   │   ├── config.py                # pydantic-settings (reads .env)
│   │   ├── security.py              # bcrypt, JWT encode/decode
│   │   └── rate_limiter.py          # slowapi Limiter singleton
│   ├── db/
│   │   ├── base.py                  # SQLAlchemy DeclarativeBase
│   │   ├── session.py               # async engine + session factory
│   │   └── models/
│   │       ├── user.py              # User model
│   │       ├── task.py              # Task model (status/priority enums)
│   │       └── token.py             # RefreshToken model
│   ├── repositories/
│   │   ├── user_repo.py             # User CRUD
│   │   ├── task_repo.py             # Task CRUD with filters
│   │   └── token_repo.py            # RefreshToken create/get/revoke
│   ├── services/
│   │   ├── auth_service.py          # register, login, refresh logic
│   │   └── task_service.py          # task business logic
│   └── schemas/
│       ├── auth.py                  # UserCreate, UserOut, TokenResponse, ...
│       └── task.py                  # TaskCreate, TaskUpdate, TaskOut, TaskListResponse
├── migrations/
│   ├── env.py                       # Alembic async env (run_sync pattern)
│   ├── script.py.mako               # migration template
│   └── versions/
│       └── 0001_initial.py          # initial schema: users, tasks, refresh_tokens
├── tests/
│   ├── conftest.py                  # async client fixture, auth_headers fixture
│   ├── unit/test_security.py
│   └── integration/
│       ├── test_auth.py
│       └── test_tasks.py
├── scripts/start.sh                 # Render entrypoint: alembic upgrade head + uvicorn
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── requirements-dev.txt
└── .env.example
```

---

## Key technical decisions

### Clean Architecture (Routers → Services → Repositories)
Strict layer separation means routers never touch the DB, and repositories never contain business logic. This makes each layer independently testable and replaceable.

### Refresh token rotation
Each refresh generates a new access token and revokes the used refresh token. Tokens are stored in `refresh_tokens` table so they can be invalidated server-side (unlike stateless JWTs). Expiry is validated in Python to avoid SQLite/PostgreSQL timezone comparison differences.

### `native_enum=False` for task enums
SQLAlchemy enums use `VARCHAR` storage instead of PostgreSQL native `ENUM` types. This allows the same models to work against both PostgreSQL in production and SQLite in-memory during tests — no separate test models needed.

### Alembic with async SQLAlchemy
`migrations/env.py` uses the `connection.run_sync(do_run_migrations)` pattern to bridge the async engine with Alembic's synchronous migration runner.

### SSL configuration
`POSTGRES_SSL=true` passes `ssl="require"` via asyncpg `connect_args` for production connections to Neon. Defaults to `false` so local and Docker setups work without extra configuration. Set it to `true` in the Render dashboard alongside the Neon credentials.

### `exclude_unset=True` for PATCH
Pydantic's `model_dump(exclude_unset=True)` ensures only explicitly sent fields are updated. Sending `{}` leaves the task unchanged; sending `{"description": null}` explicitly clears the description.

---

## Deployment (Render + Neon)

1. Create a [Neon](https://neon.tech) project and copy the host/credentials
2. Deploy this repo on [Render](https://render.com) as a Web Service
3. Set environment variables in Render dashboard (see `.env.example`)
4. On first deploy, `start.sh` runs `alembic upgrade head` automatically

---

## Tech stack

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI 0.115 + Pydantic v2 |
| ORM | SQLAlchemy 2.0 (async) + asyncpg |
| Migrations | Alembic 1.14 |
| Auth | python-jose (JWT) + passlib (bcrypt) |
| Rate limiting | slowapi |
| Database (prod) | PostgreSQL via Neon |
| Database (test) | SQLite in-memory via aiosqlite |
| Infra | Docker Compose (dev) · Render (prod) |
| Tests | Pytest + pytest-asyncio + httpx |
