# PinMe API

Backend for **PinMe** — a drawing-practice platform that helps artists work through their own reference boards with timed, non-repeating sessions and progress tracking.

Companion frontend (planned): `pin-me-web`  
Product docs hub (private/local): `pin-me`

---

## Problem

Artists often keep reference images in messy folders or boards, then redraw the same favorites. PinMe is being built so you can:

- organize references into boards,
- run timed practice sessions,
- mark images **Complete** or **Skip**,
- only re-draw from the **available** pool until a board reset,
- later: stats (GitHub-style heatmap) and user-owned Drive/Pinterest media.

This repository is the **REST API** that will own that logic, persistence, and (bootstrap) file storage.

---

## Current status

| Item | State |
|------|--------|
| Stage | **001 — API skeleton** |
| Production-ready? | No — early scaffolding |
| Implemented | FastAPI app, `/health`, settings, SQLAlchemy + Alembic wiring, Docker Compose (Postgres 16 + S3-compatible mock), Pytest smoke |
| Next | Boards CRUD, image upload (S3 API), practice session engine |

---

## Tech stack

| Layer | Choice |
|-------|--------|
| Language | Python 3.12+ |
| Framework | FastAPI + Uvicorn |
| ORM / migrations | SQLAlchemy 2 + Alembic |
| Database | PostgreSQL 16 |
| Bootstrap object storage | S3-compatible local mock (`adobe/s3mock`; MinIO if pullable; Cloudflare R2 later) |
| Config | pydantic-settings + `.env` |
| Tests | Pytest + httpx / TestClient |
| Containers | Docker Compose + Dockerfile (deploy-shaped) |

---

## Architecture (sketch)

```text
Client (pin-me-web)
        │ REST
        ▼
   PinMe API (this repo)
        ├── PostgreSQL   → users, boards, progress, sessions (coming soon)
        └── S3 API       → LOCAL_UPLOAD bootstrap only (local mock / MinIO → R2)
```

Long-term: image **binaries** stay on the user’s Google Drive / Pinterest; this API keeps metadata, practice history, and stats.

### Diagrams & screenshots

Place future architecture diagrams and demo screenshots in [`docs/images/`](docs/images/). Link them here as the project grows.

---

## Getting started

### Prerequisites

- Python 3.12+ (3.13 works for local dev)
- Docker Desktop (or compatible Docker Engine)
- Git

### 1. Clone and enter the repo

```bash
cd pin-me-api
```

### 2. Environment file

```bash
cp .env.example .env
```

Defaults match `docker-compose.yml` (Postgres + MinIO on localhost).

### 3. Start infrastructure

```bash
docker compose up -d
```

Services:

- Postgres → `localhost:5433` (user/password/db: `pinme`) — host port **5433** avoids clashes with a local Postgres on 5432
- S3 mock → `localhost:9090` with initial bucket `pin-me`

> Note: MinIO images could not be pulled in the original Stage 001 environment (`minio/*` registry denied). Compose therefore uses `adobe/s3mock` so the S3 API path stays valid. You can swap back to MinIO later if your Docker registry allows it.

### 4. Python virtualenv and dependencies

```bash
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# macOS / Linux
# source .venv/bin/activate

pip install -r requirements-dev.txt
```

### 5. Run migrations

```bash
alembic upgrade head
```

Stage 001 ships an empty schema stub so Alembic is ready for domain tables next.

### 6. Start the API

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Health: [http://localhost:8000/health](http://localhost:8000/health)
- OpenAPI docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Testing

```bash
pytest
```

**Covered today**

- `GET /health` returns `{"status":"ok"}`
- Root route exposes the health path

**How this stage was verified**

Local smoke: `docker compose up -d`, `alembic upgrade head`, `pytest` (2 passed), `GET /health` → `{"status":"ok"}`.

---

## Project structure

```text
pin-me-api/
├── app/
│   ├── api/          # HTTP routers (health first)
│   ├── core/         # settings
│   ├── db/           # SQLAlchemy engine/session/base
│   └── main.py       # FastAPI entrypoint
├── alembic/          # migrations
├── tests/
├── docs/
│   └── images/       # diagrams / screenshots (future)
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── requirements-dev.txt
```

---

## Stages / changelog

| Stage | Date | Summary |
|-------|------|---------|
| 001 | 2026-10-03 | API skeleton: FastAPI, Compose (Postgres + S3 mock), Alembic, health + Pytest |

---

## Roadmap (API)

- Boards + bootstrap image upload via S3 API (local mock/MinIO → R2)
- Practice sessions (queue-at-start, Complete / Skip, reset with history)
- Auth (JWT) and resume unfinished sessions
- Activity heatmap stats endpoint
- Later: Google Drive / Pinterest as user-owned media sources

---

## Related repositories

| Repo | Role |
|------|------|
| `pin-me-web` | Next.js UI (Stage 002 skeleton) |
| `pin-me` | Private/local product docs hub (not the public portfolio face) |

---

## License

Personal / portfolio project — license TBD.
