from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.boards import router as boards_router
from app.api.health import router as health_router
from app.api.images import router as images_router
from app.api.practice import router as practice_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
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
