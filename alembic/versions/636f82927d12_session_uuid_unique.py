"""session_uuid unique

Revision ID: 636f82927d12
Revises: a6c3830d63a9
Create Date: 2026-10-10 19:51:33.760005

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '636f82927d12'
down_revision: Union[str, Sequence[str], None] = 'a6c3830d63a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint("uq_session_session_uuid", "session", ["session_uuid"])


def downgrade() -> None:
    op.drop_constraint("uq_session_session_uuid", "session", type_="unique")
