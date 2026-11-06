"""create login_session

Revision ID: 4a84642b48c1
Revises: 4ed3809d84c9
Create Date: 2026-10-11 01:23:42.818459

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '4a84642b48c1'
down_revision: Union[str, Sequence[str], None] = '4ed3809d84c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # Eski, yanlış kurulmuş tabloları temizle (sadece boşsa)
    for old in ("loging_session", "loging_section"):
        if sa.inspect(conn).has_table(old):
            count = conn.execute(sa.text(f'select count(*) from public."{old}"')).scalar()
            if count and count > 0:
                raise RuntimeError(f"{old} dolu ({count} satır), silinmedi. Önce incele.")
            op.drop_table(old)

    if sa.inspect(conn).has_table("login_session"):
        return

    op.create_table(
        "login_session",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_login_session_user_id", "login_session", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_login_session_user_id", table_name="login_session")
    op.drop_table("login_session")
