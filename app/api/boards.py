from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_demo_user
from app.models.user import User
from app.schemas.board import BoardCreate, BoardRead, BoardUpdate
from app.schemas.image import ImageRead
from app.schemas.practice import ResetProgressResult
from app.services import boards as board_service
from app.services import images as image_service
from app.services import practice as practice_service

router = APIRouter(prefix="/boards", tags=["boards"])


@router.get("", response_model=list[BoardRead])
def list_boards(
    db: Session = Depends(get_db),
    user: User = Depends(get_demo_user),
) -> list[BoardRead]:
    return board_service.list_boards(db, user.id)


@router.post("", response_model=BoardRead, status_code=201)
def create_board(
    payload: BoardCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_demo_user),
) -> BoardRead:
    return board_service.create_board(db, user.id, payload)


@router.get("/{board_id}", response_model=BoardRead)
def get_board(
    board_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_demo_user),
) -> BoardRead:
    return board_service.get_board(db, user.id, board_id)


@router.patch("/{board_id}", response_model=BoardRead)
def update_board(
    board_id: uuid.UUID,
    payload: BoardUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_demo_user),
) -> BoardRead:
    return board_service.update_board(db, user.id, board_id, payload)


@router.delete("/{board_id}", status_code=204)
def delete_board(
    board_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_demo_user),
) -> None:
    board_service.delete_board(db, user.id, board_id)


@router.get("/{board_id}/images", response_model=list[ImageRead])
def list_board_images(
    board_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_demo_user),
) -> list[ImageRead]:
    return image_service.list_images(db, user.id, board_id)


@router.post("/{board_id}/images", response_model=ImageRead, status_code=201)
async def upload_board_image(
    board_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_demo_user),
) -> ImageRead:
    return await image_service.upload_image(db, user.id, board_id, file)


@router.delete("/{board_id}/images/{image_id}", status_code=204)
def delete_board_image(
    board_id: uuid.UUID,
    image_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_demo_user),
) -> None:
    image_service.delete_image(db, user.id, board_id, image_id)


@router.post("/{board_id}/reset-progress", response_model=ResetProgressResult)
def reset_board_progress(
    board_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_demo_user),
) -> ResetProgressResult:
    return practice_service.reset_board_progress(db, user.id, board_id)
