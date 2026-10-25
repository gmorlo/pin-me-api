import uuid

# Seeded allowlisted identity (Alembic 0002). Prefer Google login or AUTH_DEV_BYPASS.
DEMO_USER_ID = uuid.UUID("00000000-0000-4000-8000-000000000001")
DEMO_USER_EMAIL = "demo@pinme.local"
DEMO_USER_USERNAME = "demo"

ALLOWED_IMAGE_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_IMAGES_PER_BOARD = 50
