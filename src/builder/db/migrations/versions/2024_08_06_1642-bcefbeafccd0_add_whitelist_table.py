"""add whitelist table

Revision ID: bcefbeafccd0
Revises: 0074a28b6b64
Create Date: 2024-08-06 16:42:10.382732

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'bcefbeafccd0'
down_revision = '0074a28b6b64'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'whitelist',
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('user_id'),
        sa.UniqueConstraint('user_id'),
    )


def downgrade() -> None:
    op.drop_table('whitelist')
