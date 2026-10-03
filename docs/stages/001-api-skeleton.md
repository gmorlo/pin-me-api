# Stage 001 — API skeleton

- **Date:** 2026-10-03
- **Status:** done
- **Repo:** pin-me-api

## Goal

Bootstrap a runnable FastAPI service with local Postgres + S3-compatible storage, Alembic wiring, and a health check — without domain features yet.

## What changed

- FastAPI app with `GET /health` and root metadata route
- `pydantic-settings` config aligned with `.env.example`
- SQLAlchemy engine/session + declarative `Base`
- Alembic with initial empty migration stub `0001_initial`
- Docker Compose: Postgres 16 (host port 5433) + `adobe/s3mock` (bucket `pin-me`)
- Dockerfile for future deploy/prod-like runs
- Pytest smoke tests for health/root
- Portfolio README + `docs/images/` placeholder

## Environment

- Local dev: API on host (Uvicorn), Postgres + S3 mock via Docker Compose
- Python 3.13 in this machine’s venv (3.12+ supported; Dockerfile uses 3.12)
- Not deployed to cloud in this stage

## How tested

```bash
docker compose up -d
python -m venv .venv
# activate venv, then:
pip install -r requirements-dev.txt
cp .env.example .env
alembic upgrade head
pytest
uvicorn app.main:app --host 127.0.0.1 --port 8000
# GET http://127.0.0.1:8000/health → {"status":"ok"}
```

## Results

| Check | Result |
|-------|--------|
| `docker compose up -d` | Postgres healthy on `:5433`, S3 mock on `:9090` |
| `alembic upgrade head` | Applied `0001_initial` stub |
| `pytest` | **2 passed** |
| `GET /health` via Uvicorn | **200** `{"status":"ok"}` |

### Known issues

- Docker Hub denied pulls for `minio/minio` / `minio/mc` here → local S3 uses `adobe/s3mock` instead (same S3_* settings pattern).
- Host port **5433** used because something already answered on `5432` with different credentials.

## Next stage

Web skeleton (`pin-me-web`) and/or boards + upload vertical slice on the API.
