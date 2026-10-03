from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.board import Board
from app.models.image import ReferenceImage


def list_boards(db: Session, user_id: uuid.UUID) -> list[tuple[Board, int]]:
    image_count = func.count(ReferenceImage.id)
    stmt = (
        select(Board, image_count)
        .outerjoin(ReferenceImage, ReferenceImage.board_id == Board.id)
        .where(Board.user_id == user_id)
        .group_by(Board.id)
        .order_by(Board.created_at.desc())
    )
    return list(db.execute(stmt).all())


def get_board(db: Session, board_id: uuid.UUID, user_id: uuid.UUID) -> Board | None:
    return db.scalar(
        select(Board).where(Board.id == board_id, Board.user_id == user_id)
    )


def count_images(db: Session, board_id: uuid.UUID) -> int:
    return int(
        db.scalar(
            select(func.count()).select_from(ReferenceImage).where(
                ReferenceImage.board_id == board_id
            )
        )
        or 0
    )


def create_board(
    db: Session, *, user_id: uuid.UUID, name: str, description: str | None
) -> Board:
    board = Board(user_id=user_id, name=name, description=description)
    db.add(board)
    db.commit()
    db.refresh(board)
    return board


def update_board(db: Session, board: Board, **fields: object) -> Board:
    for key, value in fields.items():
        if value is not None or key == "description":
            setattr(board, key, value)
    db.add(board)
    db.commit()
    db.refresh(board)
    return board


def delete_board(db: Session, board: Board) -> None:
    db.delete(board)
    db.commit()
