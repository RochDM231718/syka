"""add rejection reason

Revision ID: add_rejection_reason
Revises: fix_enums
Create Date: 2023-10-27 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'add_rejection_reason'
down_revision = 'fix_enums'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('achievements', sa.Column('rejection_reason', sa.Text(), nullable=True))

def downgrade() -> None:
    op.drop_column('achievements', 'rejection_reason')