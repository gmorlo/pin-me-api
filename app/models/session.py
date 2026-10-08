from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.image import ReferenceImage


class SessionStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    FINISHED = "FINISHED"
    CANCELLED = "CANCELLED"


class SessionImageStatus(str, enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    SKIPPED = "SKIPPED"


class PracticeSession(Base):
    __tablename__ = "practice_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    board_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("boards.id", ondelete="CASCADE"), nullable=False
    )
    duration_per_image_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    image_count: Mapped[int] = mapped_column(Integer, nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(40), nullable=False, default=SessionStatus.ACTIVE.value
    )
    total_practice_seconds: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )

    queue: Mapped[list[SessionImage]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="SessionImage.order_number",
    )


class SessionImage(Base):
    __tablename__ = "session_images"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("practice_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    image_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("reference_images.id", ondelete="CASCADE"),
        nullable=False,
    )
    order_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(40), nullable=False, default=SessionImageStatus.PENDING.value
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    elapsed_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    session: Mapped[PracticeSession] = relationship(back_populates="queue")
    image: Mapped[ReferenceImage] = relationship()


class PracticeCompletionEvent(Base):
    __tablename__ = "practice_completion_events"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    image_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("reference_images.id", ondelete="CASCADE"),
        nullable=False,
    )
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("practice_sessions.id", ondelete="SET NULL"),
        nullable=True,
    )
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
