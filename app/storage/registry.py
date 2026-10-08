from __future__ import annotations

from fastapi import HTTPException, status

from app.core.config import get_settings
from app.models.image import SourceType
from app.storage.base import ImageSource
from app.storage.local_upload import LocalUploadSource

_local_source: LocalUploadSource | None = None


def _local_upload_source() -> LocalUploadSource:
    global _local_source
    if _local_source is None:
        _local_source = LocalUploadSource(get_settings())
    return _local_source


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
    global _local_source
    _local_source = None
