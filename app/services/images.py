from __future__ import annotations

import uuid

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.constants import (
    ALLOWED_IMAGE_CONTENT_TYPES,
    MAX_IMAGES_PER_BOARD,
    MAX_UPLOAD_BYTES,
)
from app.models.image import SourceType
from app.repositories import boards as board_repo
from app.repositories import images as image_repo
from app.schemas.image import ImagePage, ImageRead
from app.storage import get_source
from app.storage.base import ResolvedContent

DEFAULT_IMAGE_PAGE_SIZE = 24
MAX_IMAGE_PAGE_SIZE = 50


def _to_read(image) -> ImageRead:
    return ImageRead(
        id=image.id,
        board_id=image.board_id,
        source_type=image.source_type,
        storage_key=image.storage_key,
        file_url=image.file_url,
        source_url=image.source_url,
        external_id=image.external_id,
        content_type=image.content_type,
        original_filename=image.original_filename,
        created_at=image.created_at,
        content_path=f"/images/{image.id}/content",
    )


def register_image(
    db: Session,
    *,
    board_id: uuid.UUID,
    user_id: uuid.UUID,
    source_type: str,
    storage_key: str | None = None,
    file_url: str | None = None,
    source_url: str | None = None,
    external_id: str | None = None,
    content_type: str | None = None,
    original_filename: str | None = None,
) -> ImageRead:
    """Shared registration path for LOCAL_UPLOAD today and remote importers later."""
    board = board_repo.get_board(db, board_id, user_id)
    if board is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board not found")
    if board_repo.count_images(db, board.id) >= MAX_IMAGES_PER_BOARD:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Board already has the maximum of {MAX_IMAGES_PER_BOARD} images",
        )
    image = image_repo.create_image(
        db,
        board_id=board.id,
        user_id=user_id,
        source_type=source_type,
        storage_key=storage_key,
        file_url=file_url,
        source_url=source_url,
        external_id=external_id,
        content_type=content_type,
        original_filename=original_filename,
    )
    return _to_read(image)


def list_images(
    db: Session,
    user_id: uuid.UUID,
    board_id: uuid.UUID,
    *,
    limit: int = DEFAULT_IMAGE_PAGE_SIZE,
    offset: int = 0,
) -> ImagePage:
    board = board_repo.get_board(db, board_id, user_id)
    if board is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board not found")
    page_size = max(1, min(limit, MAX_IMAGE_PAGE_SIZE))
    page_offset = max(0, offset)
    total = image_repo.count_images(db, board.id)
    items = [
        _to_read(image)
        for image in image_repo.list_images(
            db, board.id, limit=page_size, offset=page_offset
        )
    ]
    return ImagePage(items=items, total=total, limit=page_size, offset=page_offset)


async def upload_image(
    db: Session, user_id: uuid.UUID, board_id: uuid.UUID, file: UploadFile
) -> ImageRead:
    board = board_repo.get_board(db, board_id, user_id)
    if board is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board not found")

    content_type = (file.content_type or "").lower()
    if content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported content type. Allowed: {sorted(ALLOWED_IMAGE_CONTENT_TYPES)}",
        )

    data = await file.read()
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds {MAX_UPLOAD_BYTES} bytes",
        )

    source = get_source(SourceType.LOCAL_UPLOAD.value)
    storage_key = source.upload(
        board_id=str(board.id),
        filename=file.filename or "upload.bin",
        content_type=content_type,
        data=data,
    )
    try:
        return register_image(
            db,
            board_id=board.id,
            user_id=user_id,
            source_type=SourceType.LOCAL_UPLOAD.value,
            storage_key=storage_key,
            content_type=content_type,
            original_filename=file.filename,
        )
    except Exception:
        source.delete(storage_key)
        raise


def delete_image(
    db: Session, user_id: uuid.UUID, board_id: uuid.UUID, image_id: uuid.UUID
) -> None:
    board = board_repo.get_board(db, board_id, user_id)
    if board is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board not found")
    image = image_repo.get_image(db, image_id)
    if image is None or image.board_id != board.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    if image.storage_key:
        try:
            get_source(image.source_type).delete(image.storage_key)
        except HTTPException as exc:
            if exc.status_code != status.HTTP_501_NOT_IMPLEMENTED:
                raise
    image_repo.delete_image(db, image)


def resolve_image_content(db: Session, image_id: uuid.UUID) -> ResolvedContent:
    image = image_repo.get_image(db, image_id)
    if image is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    source = get_source(image.source_type)
    return source.resolve(image)
