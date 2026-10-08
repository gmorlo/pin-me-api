from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.progress import ProgressStatus
from app.models.session import (
    PracticeSession,
    SessionImage,
    SessionImageStatus,
    SessionStatus,
)
from app.repositories import boards as board_repo
from app.repositories import practice as practice_repo
from app.schemas.practice import (
    ActionBody,
    QueueImageRead,
    ResetProgressResult,
    SessionCreate,
    SessionRead,
)


def _queue_item(row: SessionImage) -> QueueImageRead:
    return QueueImageRead(
        id=row.id,
        image_id=row.image_id,
        order_number=row.order_number,
        status=row.status,
        content_path=f"/images/{row.image_id}/content",
        original_filename=row.image.original_filename if row.image else None,
    )


def _to_read(session: PracticeSession) -> SessionRead:
    queue = sorted(session.queue, key=lambda item: item.order_number)
    completed = sum(
        1 for item in queue if item.status == SessionImageStatus.COMPLETED.value
    )
    skipped = sum(
        1 for item in queue if item.status == SessionImageStatus.SKIPPED.value
    )
    pending = sum(
        1 for item in queue if item.status == SessionImageStatus.PENDING.value
    )
    current = next(
        (item for item in queue if item.status == SessionImageStatus.PENDING.value),
        None,
    )
    return SessionRead(
        id=session.id,
        board_id=session.board_id,
        status=session.status,
        duration_per_image_seconds=session.duration_per_image_seconds,
        image_count=session.image_count,
        started_at=session.started_at,
        finished_at=session.finished_at,
        total_practice_seconds=session.total_practice_seconds,
        current_order=current.order_number if current else None,
        completed_count=completed,
        skipped_count=skipped,
        pending_count=pending,
        current_image=_queue_item(current) if current else None,
        queue=[_queue_item(item) for item in queue],
    )


def create_session(
    db: Session, user_id: uuid.UUID, payload: SessionCreate
) -> SessionRead:
    board = board_repo.get_board(db, payload.board_id, user_id)
    if board is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board not found")

    available = practice_repo.list_available_image_ids(
        db, board_id=board.id, user_id=user_id
    )
    if not available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No AVAILABLE images on this board",
        )

    session = practice_repo.create_session_with_queue(
        db,
        user_id=user_id,
        board_id=board.id,
        duration_per_image_seconds=payload.duration_per_image_seconds,
        image_count=payload.image_count,
        available_ids=available,
    )
    return _to_read(session)


def get_session(db: Session, user_id: uuid.UUID, session_id: uuid.UUID) -> SessionRead:
    session = practice_repo.get_session(db, session_id, user_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    return _to_read(session)


def pause_session(
    db: Session, user_id: uuid.UUID, session_id: uuid.UUID
) -> SessionRead:
    session = practice_repo.get_session(db, session_id, user_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    if session.status != SessionStatus.ACTIVE.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only ACTIVE sessions can be paused",
        )
    session.status = SessionStatus.PAUSED.value
    session = practice_repo.save_session(db, session)
    return _to_read(session)


def resume_session(
    db: Session, user_id: uuid.UUID, session_id: uuid.UUID
) -> SessionRead:
    session = practice_repo.get_session(db, session_id, user_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    if session.status != SessionStatus.PAUSED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PAUSED sessions can be resumed",
        )
    session.status = SessionStatus.ACTIVE.value
    current = next(
        (
            item
            for item in session.queue
            if item.status == SessionImageStatus.PENDING.value
        ),
        None,
    )
    if current and current.started_at is None:
        current.started_at = datetime.now(timezone.utc)
    session = practice_repo.save_session(db, session)
    return _to_read(session)


def _current_pending(session: PracticeSession) -> SessionImage:
    if session.status not in {
        SessionStatus.ACTIVE.value,
        SessionStatus.PAUSED.value,
    }:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session is not active",
        )
    current = next(
        (
            item
            for item in sorted(session.queue, key=lambda row: row.order_number)
            if item.status == SessionImageStatus.PENDING.value
        ),
        None,
    )
    if current is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pending images left in this session",
        )
    return current


def _finish_if_done(session: PracticeSession) -> None:
    pending = any(
        item.status == SessionImageStatus.PENDING.value for item in session.queue
    )
    if pending:
        next_item = next(
            item
            for item in sorted(session.queue, key=lambda row: row.order_number)
            if item.status == SessionImageStatus.PENDING.value
        )
        if next_item.started_at is None:
            next_item.started_at = datetime.now(timezone.utc)
        return
    session.status = SessionStatus.FINISHED.value
    session.finished_at = datetime.now(timezone.utc)


def complete_current(
    db: Session,
    user_id: uuid.UUID,
    session_id: uuid.UUID,
    body: ActionBody,
) -> SessionRead:
    session = practice_repo.get_session(db, session_id, user_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    current = _current_pending(session)
    now = datetime.now(timezone.utc)
    if current.started_at is None:
        current.started_at = now
    current.finished_at = now
    current.elapsed_seconds = body.elapsed_seconds
    current.status = SessionImageStatus.COMPLETED.value
    session.total_practice_seconds += body.elapsed_seconds

    progress = practice_repo.get_or_create_progress(
        db, user_id=user_id, image_id=current.image_id
    )
    progress.status = ProgressStatus.COMPLETED.value
    progress.completed_at = now
    progress.completion_count += 1
    practice_repo.add_completion_event(
        db,
        user_id=user_id,
        image_id=current.image_id,
        session_id=session.id,
    )
    _finish_if_done(session)
    session = practice_repo.save_session(db, session)
    return _to_read(session)


def skip_current(
    db: Session,
    user_id: uuid.UUID,
    session_id: uuid.UUID,
    body: ActionBody,
) -> SessionRead:
    session = practice_repo.get_session(db, session_id, user_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    current = _current_pending(session)
    now = datetime.now(timezone.utc)
    if current.started_at is None:
        current.started_at = now
    current.finished_at = now
    current.elapsed_seconds = body.elapsed_seconds
    current.status = SessionImageStatus.SKIPPED.value
    session.total_practice_seconds += body.elapsed_seconds
    # Global progress stays AVAILABLE.
    _finish_if_done(session)
    session = practice_repo.save_session(db, session)
    return _to_read(session)


def finish_session(
    db: Session, user_id: uuid.UUID, session_id: uuid.UUID
) -> SessionRead:
    session = practice_repo.get_session(db, session_id, user_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    if session.status == SessionStatus.FINISHED.value:
        return _to_read(session)
    session.status = SessionStatus.FINISHED.value
    session.finished_at = datetime.now(timezone.utc)
    session = practice_repo.save_session(db, session)
    return _to_read(session)


def reset_board_progress(
    db: Session, user_id: uuid.UUID, board_id: uuid.UUID
) -> ResetProgressResult:
    board = board_repo.get_board(db, board_id, user_id)
    if board is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board not found")
    reset_count = practice_repo.reset_board_progress(
        db, board_id=board.id, user_id=user_id
    )
    return ResetProgressResult(board_id=board.id, reset_count=reset_count)
