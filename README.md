# User Management REST API

A containerized CRUD REST API for user records (`id`, `name`, `age`, `birth_state`).

**Stack:** Python 3.12 · FastAPI · SQLAlchemy 2 · Alembic · PostgreSQL 16 · Docker Compose · pytest · ruff · mypy · GitHub Actions

## Run

```bash
docker compose up --build
```

API: <http://localhost:8000> · Swagger UI: <http://localhost:8000/docs> · Health: <http://localhost:8000/health>

Postgres data lives in the named volume `pgdata`, so records survive `docker compose restart` and `down`
(only `down -v` deletes them). Migrations run automatically on API start.

## Configuration and secrets

No secret is hardcoded. Write endpoints (POST/PUT/DELETE) require an `X-API-Key` header; reads are public.

- **API key:** set `API_KEYS=key1,key2` (env var or `.env`). If unset, the API generates a random key at startup and
  prints it once in its logs: `docker compose logs api | grep generated_api_key`. Auth is never disabled.
- **Database:** the Postgres container is not published to the host (only reachable by the API on the private compose
  network), and the API port is bound to `127.0.0.1`. Its fallback password is a local convenience; set
  `POSTGRES_PASSWORD` for anything shared. See `.env.example`.

## API examples

```bash
# use your key: from `.env`, or the one printed in the API logs at startup
K="X-API-Key: $API_KEY"; J='Content-Type: application/json'

# Create (birth_state accepts a 2-letter code or full name; stored as the code)
curl -X POST localhost:8000/api/users -H "$K" -H "$J" -d '{"name":"Ada Lovelace","age":36,"birth_state":"Ohio"}'

curl localhost:8000/api/users                       # list all
curl localhost:8000/api/users/1                     # get one
curl -X PUT localhost:8000/api/users/1 -H "$K" -H "$J" -d '{"name":"Ada L.","age":37,"birth_state":"OH"}'
curl -X DELETE localhost:8000/api/users/1 -H "$K"   # 204

# Filtering, sorting, pagination (total count returned in X-Total-Count header)
curl "localhost:8000/api/users?birth_state=OH&sort_by=age&order=desc&limit=10&offset=0"
curl "localhost:8000/api/users?name=ada&min_age=20&max_age=60"
```

| Status | Meaning |
|---|---|
| 201 / 200 / 204 | Created / OK / Deleted |
| 401 / 403 | Missing / invalid API key |
| 404 | User not found |
| 422 | Validation error (bad age, unknown state, extra fields, bad query params) |
| 503 / 500 | DB unavailable / unexpected error (no internals leaked) |

Validation: name 1–100 chars (trimmed), age integer 0–150, birth state must be one of the 50 U.S. states.

## Tests

Integration tests exercise the real HTTP stack against a database (CRUD, invalid input, missing users,
state filtering, pagination, auth, health) plus unit tests.

```bash
make test        # in Docker against a throwaway Postgres (no setup needed)

# or locally (SQLite in-memory by default)
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest --cov=app
ruff check . && mypy app && pip-audit -r requirements.txt
```

CI (`.github/workflows/ci.yml`) runs lint, type check, tests on Postgres with a 90% coverage gate,
a dependency vulnerability audit, and a Docker build + health smoke test.

## Architecture decisions

- **Layers:** `routers` (HTTP) → `repository` (queries) → `models` (ORM); `schemas` hold validation. Keeps handlers thin and logic testable.
- **FastAPI + Pydantic:** declarative validation and auto-generated OpenAPI docs.
- **PostgreSQL + Alembic:** versioned schema migrations rather than implicit table creation.
- **Birth state normalized** to a 2-letter code so filtering is exact and indexed.
- **PUT is full replacement**; unknown fields are rejected (`extra=forbid`) to prevent mass-assignment surprises.
- **Security/ops hardening:** constant-time API-key checks, non-root container user, security headers, structured JSON logs with
  per-request `X-Request-ID`, a DB-aware `/health` endpoint (also the container HEALTHCHECK), and dependency auditing in CI.
- **Tests never touch real data:** the compose `tests` profile uses a separate, tmpfs-backed Postgres.

## AI assistance

Claude Code (Anthropic) generated the initial code, tests and docs from the challenge brief. I validated it by reviewing
all code, running the full test suite locally and in Docker against Postgres, running ruff/mypy/pip-audit, and manually
testing the live container with curl, including a restart to confirm data persistence.
