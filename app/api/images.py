from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user
from app.models.user import User
from app.services import images as image_service

router = APIRouter(prefix="/images", tags=["images"])


@router.get("/{image_id}/content")
def get_image_content(
    image_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    resolved = image_service.resolve_image_content(db, image_id, user.id)
    return Response(
        content=resolved.data,
        media_type=resolved.content_type,
        headers={
            "Cache-Control": "private, max-age=3600",
            "X-Content-Type-Options": "nosniff",
        },
    )
