from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SessionCreate(BaseModel):
    board_id: uuid.UUID
    duration_per_image_seconds: int = Field(ge=10, le=3600)
    image_count: int = Field(ge=1, le=100)


class ActionBody(BaseModel):
    elapsed_seconds: int = Field(default=0, ge=0, le=3600)


class QueueImageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    image_id: uuid.UUID
    order_number: int
    status: str
    content_path: str
    original_filename: str | None = None


class SessionRead(BaseModel):
    id: uuid.UUID
    board_id: uuid.UUID
    status: str
    duration_per_image_seconds: int
    image_count: int
    started_at: datetime
    finished_at: datetime | None
    total_practice_seconds: int
    current_order: int | None
    completed_count: int
    skipped_count: int
    pending_count: int
    current_image: QueueImageRead | None
    queue: list[QueueImageRead]


class ResetProgressResult(BaseModel):
    board_id: uuid.UUID
    reset_count: int
