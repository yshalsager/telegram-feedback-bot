"""Add outgoing to mapping table

Revision ID: f014515d9447
Revises: b044ab5fcf05
Create Date: 2024-08-12 12:47:08.452854

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'f014515d9447'
down_revision = 'b044ab5fcf05'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'mappings',
        sa.Column(
            'outgoing', sa.Boolean(), nullable=False, server_default=sa.sql.expression.false()
        ),
    )


def downgrade() -> None:
    op.drop_column('mappings', 'outgoing')
