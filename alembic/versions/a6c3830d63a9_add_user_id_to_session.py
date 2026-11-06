"""add user_id to session

Revision ID: a6c3830d63a9
Revises: bc306456cb44
Create Date: 2026-10-10 19:44:31.311509

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a6c3830d63a9'
down_revision: Union[str, Sequence[str], None] = 'bc306456cb44'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column("session", sa.Column("user_id", sa.Integer(), nullable=True))
    op.create_index("ix_session_user_id", "session", ["user_id"])
    op.create_foreign_key(
        "fk_session_user_id_users", "session", "users", ["user_id"], ["id"]
    )


def downgrade() -> None:
    op.drop_constraint("fk_session_user_id_users", "session", type_="foreignkey")
    op.drop_index("ix_session_user_id", table_name="session")
    op.drop_column("session", "user_id")
