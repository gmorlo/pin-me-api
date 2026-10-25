from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.practice import ActionBody, SessionCreate, SessionRead
from app.services import practice as practice_service

router = APIRouter(prefix="/practice", tags=["practice"])


@router.post("/sessions", response_model=SessionRead, status_code=201)
def create_session(
    payload: SessionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SessionRead:
    return practice_service.create_session(db, user.id, payload)


@router.get("/sessions/{session_id}", response_model=SessionRead)
def get_session(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SessionRead:
    return practice_service.get_session(db, user.id, session_id)


@router.post("/sessions/{session_id}/pause", response_model=SessionRead)
def pause_session(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SessionRead:
    return practice_service.pause_session(db, user.id, session_id)


@router.post("/sessions/{session_id}/resume", response_model=SessionRead)
def resume_session(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SessionRead:
    return practice_service.resume_session(db, user.id, session_id)


@router.post("/sessions/{session_id}/complete", response_model=SessionRead)
def complete_session_image(
    session_id: uuid.UUID,
    body: ActionBody | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SessionRead:
    return practice_service.complete_current(
        db, user.id, session_id, body or ActionBody()
    )


@router.post("/sessions/{session_id}/skip", response_model=SessionRead)
def skip_session_image(
    session_id: uuid.UUID,
    body: ActionBody | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SessionRead:
    return practice_service.skip_current(
        db, user.id, session_id, body or ActionBody()
    )


@router.post("/sessions/{session_id}/finish", response_model=SessionRead)
def finish_session(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SessionRead:
    return practice_service.finish_session(db, user.id, session_id)
