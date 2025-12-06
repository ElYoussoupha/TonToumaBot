"""Initial migration

Revision ID: 5252b0c802d2
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = '5252b0c802d2'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Tables should already exist if created by SQLAlchemy
    # This is a placeholder for the initial migration
    pass


def downgrade() -> None:
    pass
