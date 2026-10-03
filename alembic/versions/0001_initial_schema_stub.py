"""Initial schema stub — domain tables arrive in later stages.

Revision ID: 0001_initial
Revises:
Create Date: 2026-10-03

"""

from typing import Sequence, Union

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # No tables yet — Alembic is wired for upcoming board/practice migrations.
    pass


def downgrade() -> None:
    pass
