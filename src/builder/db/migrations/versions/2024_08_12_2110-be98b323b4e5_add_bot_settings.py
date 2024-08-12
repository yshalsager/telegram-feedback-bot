"""Add bot settings

Revision ID: be98b323b4e5
Revises: bcefbeafccd0
Create Date: 2024-08-12 21:10:16.820286

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'be98b323b4e5'
down_revision = 'bcefbeafccd0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add the new settings column
    op.add_column('bots', sa.Column('settings', sa.JSON(), nullable=True))

    # Create a temp table reference
    bots = sa.table(
        'bots',
        sa.column('id', sa.Integer),
        sa.column('start_message', sa.String),
        sa.column('received_message', sa.String),
        sa.column('sent_message', sa.String),
        sa.column('settings', sa.JSON),
    )

    # Migrate existing data
    connection = op.get_bind()
    for bot in connection.execute(bots.select()):
        settings = {
            'start_message': bot.start_message,
            'received_message': bot.received_message,
            'sent_message': bot.sent_message,
        }
        connection.execute(bots.update().where(bots.c.id == bot.id).values(settings=settings))

    # Make settings column not nullable
    with op.batch_alter_table('bots') as batch_op:
        batch_op.alter_column('settings', nullable=False)

    # Drop old columns
    op.drop_column('bots', 'sent_message')
    op.drop_column('bots', 'received_message')
    op.drop_column('bots', 'start_message')


def downgrade() -> None:
    # Add back the old columns
    op.add_column('bots', sa.Column('start_message', sa.VARCHAR(length=4096), nullable=True))
    op.add_column('bots', sa.Column('received_message', sa.VARCHAR(length=4096), nullable=True))
    op.add_column('bots', sa.Column('sent_message', sa.VARCHAR(length=4096), nullable=True))

    # Create a temp table reference
    bots = sa.table(
        'bots',
        sa.column('id', sa.Integer),
        sa.column('start_message', sa.String),
        sa.column('received_message', sa.String),
        sa.column('sent_message', sa.String),
        sa.column('settings', sa.JSON),
    )

    # Migrate data back to old columns
    connection = op.get_bind()
    for bot in connection.execute(bots.select()):
        if bot.settings:
            settings = bot.settings
            connection.execute(
                bots.update()
                .where(bots.c.id == bot.id)
                .values(
                    start_message=settings.get('start_message'),
                    received_message=settings.get('received_message'),
                    sent_message=settings.get('sent_message'),
                )
            )

    # Drop the settings column
    op.drop_column('bots', 'settings')
