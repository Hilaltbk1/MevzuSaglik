"""users role ve is_active

Revision ID: 4ed3809d84c9
Revises: 636f82927d12
Create Date: 2026-10-11 01:08:06.755739

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4ed3809d84c9'
down_revision: Union[str, Sequence[str], None] = '636f82927d12'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("alter table public.users add column if not exists role text not null default 'user'")
    op.execute("alter table public.users add column if not exists is_active boolean not null default true")
    op.execute("update public.users set is_active = true where is_active is null")
    op.execute("alter table public.users alter column role set default 'user'")
    op.execute("alter table public.users alter column is_active set default true")
    op.execute("alter table public.users alter column is_active set not null")
    op.execute("""
        do $$
        begin
          if not exists (select 1 from pg_constraint where conname = 'ck_users_role') then
            alter table public.users add constraint ck_users_role check (role in ('user', 'admin'));
          end if;
        end $$;
    """)


def downgrade() -> None:
    op.execute("alter table public.users drop constraint if exists ck_users_role")
    op.execute("alter table public.users drop column if exists is_active")
    op.execute("alter table public.users drop column if exists role")
