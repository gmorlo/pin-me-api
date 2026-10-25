from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.boards import router as boards_router
from app.api.health import router as health_router
from app.api.images import router as images_router
from app.api.practice import router as practice_router
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services import auth as auth_service

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if settings.allowlist_seed_email.strip():
        db = SessionLocal()
        try:
            auth_service.ensure_allowlist_user(db, settings.allowlist_seed_email)
        finally:
            db.close()
    yield


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(boards_router)
app.include_router(images_router)
app.include_router(practice_router)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": settings.app_name,
        "docs": "/docs",
        "health": "/health",
    }
