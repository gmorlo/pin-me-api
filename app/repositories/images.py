from __future__ import annotations

import uuid
from collections import defaultdict

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.image import ReferenceImage
from app.models.progress import PracticeProgress, ProgressStatus


def list_images(
    db: Session,
    board_id: uuid.UUID,
    *,
    limit: int | None = None,
    offset: int = 0,
) -> list[ReferenceImage]:
    stmt = (
        select(ReferenceImage)
        .where(ReferenceImage.board_id == board_id)
        .order_by(ReferenceImage.created_at.desc())
        .offset(offset)
    )
    if limit is not None:
        stmt = stmt.limit(limit)
    return list(db.scalars(stmt).all())


def count_images(db: Session, board_id: uuid.UUID) -> int:
    return int(
        db.scalar(
            select(func.count())
            .select_from(ReferenceImage)
            .where(ReferenceImage.board_id == board_id)
        )
        or 0
    )


def list_images_for_boards(
    db: Session, board_ids: list[uuid.UUID]
) -> dict[uuid.UUID, list[ReferenceImage]]:
    if not board_ids:
        return {}
    rows = db.scalars(
        select(ReferenceImage).where(ReferenceImage.board_id.in_(board_ids))
    ).all()
    grouped: dict[uuid.UUID, list[ReferenceImage]] = defaultdict(list)
    for image in rows:
        grouped[image.board_id].append(image)
    return grouped


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
