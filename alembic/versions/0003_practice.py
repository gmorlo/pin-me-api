"""Practice sessions, session images, completion events.

Revision ID: 0003_practice
Revises: 0002_boards
Create Date: 2026-10-08

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_practice"
down_revision: Union[str, None] = "0002_boards"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "practice_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("board_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("duration_per_image_seconds", sa.Integer(), nullable=False),
        sa.Column("image_count", sa.Integer(), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column(
            "total_practice_seconds",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["board_id"], ["boards.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_practice_sessions_user_id", "practice_sessions", ["user_id"])
    op.create_index("ix_practice_sessions_board_id", "practice_sessions", ["board_id"])

    op.create_table(
        "session_images",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("image_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "elapsed_seconds", sa.Integer(), server_default="0", nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["image_id"], ["reference_images.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["session_id"], ["practice_sessions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_session_images_session_id", "session_images", ["session_id"])

    op.create_table(
        "practice_completion_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("image_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["image_id"], ["reference_images.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["session_id"], ["practice_sessions.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_practice_completion_events_user_id",
        "practice_completion_events",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_practice_completion_events_user_id",
        table_name="practice_completion_events",
    )
    op.drop_table("practice_completion_events")
    op.drop_index("ix_session_images_session_id", table_name="session_images")
    op.drop_table("session_images")
    op.drop_index("ix_practice_sessions_board_id", table_name="practice_sessions")
    op.drop_index("ix_practice_sessions_user_id", table_name="practice_sessions")
    op.drop_table("practice_sessions")
