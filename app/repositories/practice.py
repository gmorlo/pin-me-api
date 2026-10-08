from __future__ import annotations

import random
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.image import ReferenceImage
from app.models.progress import PracticeProgress, ProgressStatus
from app.models.session import (
    PracticeCompletionEvent,
    PracticeSession,
    SessionImage,
    SessionImageStatus,
    SessionStatus,
)


def list_available_image_ids(
    db: Session, *, board_id: uuid.UUID, user_id: uuid.UUID
) -> list[uuid.UUID]:
    images = list(
        db.scalars(
            select(ReferenceImage).where(ReferenceImage.board_id == board_id)
        ).all()
    )
    if not images:
        return []

    progress_rows = {
        row.image_id: row
        for row in db.scalars(
            select(PracticeProgress).where(
                PracticeProgress.user_id == user_id,
                PracticeProgress.image_id.in_([img.id for img in images]),
            )
        ).all()
    }

    available: list[uuid.UUID] = []
    for image in images:
        row = progress_rows.get(image.id)
        if row is None or row.status == ProgressStatus.AVAILABLE.value:
            available.append(image.id)
    return available


def create_session_with_queue(
    db: Session,
    *,
    user_id: uuid.UUID,
    board_id: uuid.UUID,
    duration_per_image_seconds: int,
    image_count: int,
    available_ids: list[uuid.UUID],
) -> PracticeSession:
    sample_size = min(image_count, len(available_ids))
    chosen = random.sample(available_ids, sample_size)

    session = PracticeSession(
        user_id=user_id,
        board_id=board_id,
        duration_per_image_seconds=duration_per_image_seconds,
        image_count=sample_size,
        status=SessionStatus.ACTIVE.value,
        total_practice_seconds=0,
    )
    db.add(session)
    db.flush()

    now = datetime.now(timezone.utc)
    for index, image_id in enumerate(chosen, start=1):
        row = SessionImage(
            session_id=session.id,
            image_id=image_id,
            order_number=index,
            status=SessionImageStatus.PENDING.value,
            started_at=now if index == 1 else None,
        )
        db.add(row)

    db.commit()
    return get_session(db, session.id, user_id)  # type: ignore[return-value]


def get_session(
    db: Session, session_id: uuid.UUID, user_id: uuid.UUID
) -> PracticeSession | None:
    return db.scalar(
        select(PracticeSession)
        .where(
            PracticeSession.id == session_id,
            PracticeSession.user_id == user_id,
        )
        .options(
            selectinload(PracticeSession.queue).selectinload(SessionImage.image)
        )
    )


def save_session(db: Session, session: PracticeSession) -> PracticeSession:
    db.add(session)
    db.commit()
    return get_session(db, session.id, session.user_id)  # type: ignore[return-value]


def get_or_create_progress(
    db: Session, *, user_id: uuid.UUID, image_id: uuid.UUID
) -> PracticeProgress:
    row = db.scalar(
        select(PracticeProgress).where(
            PracticeProgress.user_id == user_id,
            PracticeProgress.image_id == image_id,
        )
    )
    if row is None:
        row = PracticeProgress(
            user_id=user_id,
            image_id=image_id,
            status=ProgressStatus.AVAILABLE.value,
            completion_count=0,
        )
        db.add(row)
        db.flush()
    return row


def add_completion_event(
    db: Session,
    *,
    user_id: uuid.UUID,
    image_id: uuid.UUID,
    session_id: uuid.UUID,
) -> None:
    db.add(
        PracticeCompletionEvent(
            user_id=user_id,
            image_id=image_id,
            session_id=session_id,
        )
    )


def reset_board_progress(
    db: Session, *, board_id: uuid.UUID, user_id: uuid.UUID
) -> int:
    image_ids = list(
        db.scalars(
            select(ReferenceImage.id).where(ReferenceImage.board_id == board_id)
        ).all()
    )
    if not image_ids:
        return 0

    rows = list(
        db.scalars(
            select(PracticeProgress).where(
                PracticeProgress.user_id == user_id,
                PracticeProgress.image_id.in_(image_ids),
            )
        ).all()
    )
    count = 0
    for row in rows:
        if (
            row.status != ProgressStatus.AVAILABLE.value
            or row.completed_at is not None
        ):
            row.status = ProgressStatus.AVAILABLE.value
            row.completed_at = None
            db.add(row)
            count += 1
    db.commit()
    return count


def count_completion_events_for_board(
    db: Session, *, board_id: uuid.UUID, user_id: uuid.UUID
) -> int:
    image_ids = list(
        db.scalars(
            select(ReferenceImage.id).where(ReferenceImage.board_id == board_id)
        ).all()
    )
    if not image_ids:
        return 0
    return len(
        list(
            db.scalars(
                select(PracticeCompletionEvent).where(
                    PracticeCompletionEvent.user_id == user_id,
                    PracticeCompletionEvent.image_id.in_(image_ids),
                )
            ).all()
        )
    )
