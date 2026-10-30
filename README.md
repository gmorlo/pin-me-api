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
- **Docker Desktop** (must be running — not only installed)
- Git
- Companion UI: `pin-me-web` (optional for API-only work)

### Local run — command by command (Windows)

Use **three terminals** if you also want the web UI. Keep this API terminal open while developing.

#### 0) Start Docker Desktop

1. Open the **Docker Desktop** app from the Start menu.
2. Wait until it says the engine is running (whale icon idle / “Engine running”).
3. If `docker compose` later fails with `dockerDesktopLinuxEngine` / pipe not found → Docker is still not ready; wait or restart Docker Desktop.

#### 1) Open this project folder

Run every command below from the `pin-me-api` root (the folder that contains `docker-compose.yml` and `app/`).

#### 2) Env file (once)

**cmd**

```bat
copy .env.example .env
```

**PowerShell**

```powershell
Copy-Item .env.example .env
```

Defaults match Compose: Postgres on `localhost:5433`, S3 mock on `localhost:9090`.

#### 3) Start Postgres + S3 mock

```bat
docker compose up -d
```

Check:

```bat
docker compose ps
```

You should see `pinme-postgres` (healthy) and `pinme-s3` (up).

| Service | Host |
|---------|------|
| Postgres | `localhost:5433` (user/password/db: `pinme`) |
| S3 mock | `localhost:9090` (bucket `pin-me` is created on first upload if missing) |

> Compose uses `adobe/s3mock` (S3-compatible). Object bytes persist in Docker volume `pinme_s3_data` (same idea as Postgres) so a container restart does not orphan DB image rows. If thumbnails 404 after an old wipe, re-upload images once. MinIO can replace S3Mock later if your registry allows those images.

#### 4) Python venv + dependencies (once, or after requirements change)

**cmd**

```bat
python -m venv .venv
.\.venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
```

**PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
```

Tip: in **cmd** use `activate.bat`. `Activate.ps1` only works in PowerShell. If activation is awkward, call tools with full path (see below).

#### 5) Database migrations

With venv active:

```bat
alembic upgrade head
```

Or without activating:

```bat
.\.venv\Scripts\alembic.exe upgrade head
```

This creates tables and seeds the temporary **demo user** (`demo@pinme.local`) used until JWT auth exists.

#### 6) Start the API (leave this running)

```bat
.\.venv\Scripts\uvicorn.exe app.main:app --reload --host 127.0.0.1 --port 8000
```

Or with venv active:

```bat
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Check in a browser:

- Health: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) → `{"status":"ok"}`
- OpenAPI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

Boards/images: `GET/POST /boards`, `/boards/{id}/images`, content at `/images/{id}/content`.

#### 7) (Optional) Start the web UI

In a **second** terminal, follow `pin-me-web` README → open [http://localhost:3000](http://localhost:3000).

### Upload limits (bootstrap LOCAL_UPLOAD)

| Cap | Value |
|-----|--------|
| Max file size | 5 MB |
| Content types | `image/jpeg`, `image/png`, `image/webp` |
| Max images per board | 50 |

Long-term binaries are meant to live on user Drive/Pinterest; S3/R2 is bootstrap only. Image handling goes through an `ImageSource` registry so remote adapters can be added without rewriting board/practice logic.

### Quick troubleshooting

| Symptom | Fix |
|---------|-----|
| `dockerDesktopLinuxEngine` / pipe error | Start/restart **Docker Desktop**, wait for engine, retry `docker compose up -d` |
| `'alembic' is not recognized` | Use `.\.venv\Scripts\alembic.exe` or run `activate.bat` first |
| Upload `NoSuchBucket` / 503 storage | Ensure `pinme-s3` is up (`docker compose ps`); restart API after Compose is healthy |
| Thumbnails `/images/.../content` 404 | Object missing in S3 (pre-volume wipe). Re-upload images, or `docker compose up -d` after pulling compose with `pinme_s3_data` |
| Port 5433 / 8000 busy | Stop the other process, or change the port in `.env` / uvicorn flag |

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
| 004 | 2026-10-08 | Practice sessions: queue-at-start, Complete/Skip, pause, reset + completion events |
| 007 | 2026-10-25 | Google OAuth + allowlist JWT cookie; local `AUTH_DEV_BYPASS` login |
| 008 | 2026-10-28 | Prod on Railway + Neon + R2: unsafe-config guard, owner-only image content, upload caps |

---

## Roadmap (API)

- Resume unfinished sessions
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
