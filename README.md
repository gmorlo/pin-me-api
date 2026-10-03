# PinMe API

Backend for **PinMe** — a drawing-practice platform that helps artists work through their own reference boards with timed, non-repeating sessions and progress tracking.

Companion frontend: `pin-me-web`  
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
| Stage | **003 — Boards + upload** |
| Production-ready? | No — early scaffolding |
| Implemented | FastAPI, `/health`, boards CRUD, LOCAL_UPLOAD via ImageSource + S3 mock, image content proxy, demo user, Pytest |
| Next | Practice sessions (queue, Complete/Skip, summary, reset) |

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

Applies domain tables (users, boards, images, progress, `board_source_links`) and seeds a temporary **demo user** (`demo@pinme.local`) used until JWT auth lands.

### 6. Start the API

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Health: [http://localhost:8000/health](http://localhost:8000/health)
- OpenAPI docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Boards: `GET/POST /boards`, images under `/boards/{id}/images`, content at `/images/{id}/content`

### Upload limits (bootstrap LOCAL_UPLOAD)

| Cap | Value |
|-----|--------|
| Max file size | 5 MB |
| Content types | `image/jpeg`, `image/png`, `image/webp` |
| Max images per board | 50 |

Long-term binaries are meant to live on user Drive/Pinterest; S3/R2 is bootstrap only. Image handling goes through an `ImageSource` registry so remote adapters can be added without rewriting board/practice logic.

---

## Testing

```bash
pytest
```

**Covered today**

- `GET /health` returns `{"status":"ok"}`
- Root route exposes the health path
- Boards CRUD + LOCAL_UPLOAD register/list/delete + content proxy (Pytest with in-memory DB + fake storage)

**How this stage was verified**

`pytest` (5 passed). With Docker Desktop running: `docker compose up -d`, `alembic upgrade head`, then exercise boards/upload against live Postgres + S3 mock.

---

## Project structure

```text
pin-me-api/
├── app/
│   ├── api/           # HTTP routers
│   ├── core/          # settings, constants
│   ├── db/            # SQLAlchemy engine/session/base
│   ├── models/        # ORM
│   ├── repositories/  # persistence
│   ├── schemas/       # Pydantic
│   ├── services/      # domain (register_image, boards)
│   ├── storage/       # ImageSource adapters + registry
│   └── main.py
├── alembic/
├── tests/
├── docs/images/       # diagrams / screenshots (future)
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
| 003 | 2026-10-03 | Boards CRUD + LOCAL_UPLOAD via ImageSource, demo user, content proxy |

---

## Roadmap (API)

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
