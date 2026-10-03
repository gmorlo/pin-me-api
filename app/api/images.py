from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services import images as image_service

router = APIRouter(prefix="/images", tags=["images"])


@router.get("/{image_id}/content")
def get_image_content(
    image_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> Response:
    resolved = image_service.resolve_image_content(db, image_id)
    return Response(
        content=resolved.data,
        media_type=resolved.content_type,
        headers={"Cache-Control": "private, max-age=3600"},
    )
