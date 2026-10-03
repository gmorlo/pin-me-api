from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.board import Board
from app.models.image import SourceType
from app.repositories import boards as board_repo
from app.repositories import images as image_repo
from app.schemas.board import BoardCreate, BoardRead, BoardUpdate
from app.storage import get_source


def _to_read(board: Board, image_count: int) -> BoardRead:
    return BoardRead(
        id=board.id,
        name=board.name,
        description=board.description,
        created_at=board.created_at,
        image_count=image_count,
    )


def list_boards(db: Session, user_id: uuid.UUID) -> list[BoardRead]:
    rows = board_repo.list_boards(db, user_id)
    return [_to_read(board, int(count or 0)) for board, count in rows]


def create_board(db: Session, user_id: uuid.UUID, payload: BoardCreate) -> BoardRead:
    board = board_repo.create_board(
        db, user_id=user_id, name=payload.name.strip(), description=payload.description
    )
    return _to_read(board, 0)


def get_board(db: Session, user_id: uuid.UUID, board_id: uuid.UUID) -> BoardRead:
    board = board_repo.get_board(db, board_id, user_id)
    if board is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board not found")
    return _to_read(board, board_repo.count_images(db, board.id))


def update_board(
    db: Session, user_id: uuid.UUID, board_id: uuid.UUID, payload: BoardUpdate
) -> BoardRead:
    board = board_repo.get_board(db, board_id, user_id)
    if board is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board not found")
    data = payload.model_dump(exclude_unset=True)
    if "name" in data and data["name"] is not None:
        data["name"] = data["name"].strip()
    board = board_repo.update_board(db, board, **data)
    return _to_read(board, board_repo.count_images(db, board.id))


def delete_board(db: Session, user_id: uuid.UUID, board_id: uuid.UUID) -> None:
    board = board_repo.get_board(db, board_id, user_id)
    if board is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board not found")
    images = image_repo.list_images(db, board.id)
    local = get_source(SourceType.LOCAL_UPLOAD.value)
    for image in images:
        if image.source_type == SourceType.LOCAL_UPLOAD.value and image.storage_key:
            local.delete(image.storage_key)
    board_repo.delete_board(db, board)
