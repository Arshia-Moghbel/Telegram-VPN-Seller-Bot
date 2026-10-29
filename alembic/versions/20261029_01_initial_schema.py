"""Create the complete application schema.

Revision ID: 20261029_01
Revises:
Create Date: 2026-10-29
"""

from alembic import op

from database import models  # noqa: F401 - registers mapped classes
from db import Base


revision = "20261029_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
