from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ImageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    board_id: uuid.UUID
    source_type: str
    storage_key: str | None
    file_url: str | None
    source_url: str | None
    external_id: str | None
    content_type: str | None
    original_filename: str | None
    created_at: datetime
    content_path: str


class ImagePage(BaseModel):
    items: list[ImageRead]
    total: int
    limit: int
    offset: int = Field(ge=0)
