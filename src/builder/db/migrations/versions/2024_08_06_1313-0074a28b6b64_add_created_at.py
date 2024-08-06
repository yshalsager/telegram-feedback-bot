"""add created and updated at

Revision ID: 0074a28b6b64
Revises: 2745ac26978e
Create Date: 2024-08-06 13:13:04.391999

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '0074a28b6b64'
down_revision = '2745ac26978e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add columns without default values
    op.add_column('bots', sa.Column('created_at', sa.DateTime(), nullable=True))
    # Update existing rows with current timestamp
    op.execute('UPDATE bots SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL')
    # Make created_at non-nullable
    with op.batch_alter_table('bots') as batch_op:
        batch_op.alter_column(
            'created_at', nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')
        )


def downgrade() -> None:
    op.drop_column('bots', 'created_at')
