from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.image import ReferenceImage
from app.models.progress import PracticeProgress, ProgressStatus


def list_images(db: Session, board_id: uuid.UUID) -> list[ReferenceImage]:
    return list(
        db.scalars(
            select(ReferenceImage)
            .where(ReferenceImage.board_id == board_id)
            .order_by(ReferenceImage.created_at.desc())
        ).all()
    )


def get_image(db: Session, image_id: uuid.UUID) -> ReferenceImage | None:
    return db.get(ReferenceImage, image_id)


def create_image(
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
) -> ReferenceImage:
    image = ReferenceImage(
        board_id=board_id,
        source_type=source_type,
        storage_key=storage_key,
        file_url=file_url,
        source_url=source_url,
        external_id=external_id,
        content_type=content_type,
        original_filename=original_filename,
    )
    db.add(image)
    db.flush()
    progress = PracticeProgress(
        user_id=user_id,
        image_id=image.id,
        status=ProgressStatus.AVAILABLE.value,
        completion_count=0,
    )
    db.add(progress)
    db.commit()
    db.refresh(image)
    return image


def delete_image(db: Session, image: ReferenceImage) -> None:
    db.delete(image)
    db.commit()
