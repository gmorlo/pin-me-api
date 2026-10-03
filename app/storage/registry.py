from __future__ import annotations

from functools import lru_cache

from fastapi import HTTPException, status

from app.core.config import get_settings
from app.models.image import SourceType
from app.storage.base import ImageSource
from app.storage.local_upload import LocalUploadSource


@lru_cache
def _local_upload_source() -> LocalUploadSource:
    return LocalUploadSource(get_settings())


def get_source(source_type: str) -> ImageSource:
    if source_type == SourceType.LOCAL_UPLOAD.value:
        return _local_upload_source()
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=(
            f"Image source '{source_type}' is not implemented yet. "
            "Stage 003 supports LOCAL_UPLOAD only; "
            "GOOGLE_DRIVE / PINTEREST adapters come later."
        ),
    )


def clear_source_cache() -> None:
    _local_upload_source.cache_clear()
