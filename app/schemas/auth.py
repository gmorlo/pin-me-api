from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    username: str
    created_at: datetime


class DevLoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)


class AuthStatus(BaseModel):
    google_configured: bool
    dev_bypass: bool
