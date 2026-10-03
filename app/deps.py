from __future__ import annotations

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import DEMO_USER_ID
from app.db.session import get_db
from app.models.user import User


def get_demo_user(db: Session = Depends(get_db)) -> User:
    """Temporary identity until JWT auth lands in V1.1."""
    user = db.scalar(select(User).where(User.id == DEMO_USER_ID))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Demo user missing — run alembic upgrade head",
        )
    return user
