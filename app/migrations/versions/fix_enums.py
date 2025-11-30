"""fix enums

Revision ID: fix_enums
Revises: update_schema_v1
Create Date: 2023-10-27 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'fix_enums'
down_revision = 'update_schema_v1' # Ссылаемся на предыдущую миграцию
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Важно: ALTER TYPE нельзя выполнять внутри транзакции в некоторых версиях PG,
    # поэтому используем autocommit_block
    with op.get_context().autocommit_block():
        # Добавляем недостающие роли
        op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'GUEST'")
        op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'STUDENT'")
        op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'MODERATOR'")

def downgrade() -> None:
    # Удалить значения из ENUM в Postgres очень сложно, обычно это не делают в даунгрейде
    pass