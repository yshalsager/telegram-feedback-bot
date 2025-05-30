"""migrate_token_encryption_format

Revision ID: 617e42e2220e
Revises: be98b323b4e5
Create Date: 2025-05-30 18:48:39.050672

"""

import base64
import logging
from os import getenv

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '617e42e2220e'
down_revision = 'be98b323b4e5'
branch_labels = None
depends_on = None

ENCRYPTION_KEY = getenv('ENCRYPTION_KEY', '')

if not ENCRYPTION_KEY:
    raise ValueError('ENCRYPTION_KEY environment variable not set')

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def xor_encrypt(data: bytes, key: bytes) -> bytes:
    """Encrypt data using XOR with the key."""
    return bytes(
        a ^ b
        for a, b in zip(data, (key * ((len(data) // len(key)) + 1))[: len(data)], strict=False)
    )


def xor_decrypt(encrypted_data: bytes, key: bytes) -> bytes:
    """Decrypt data using XOR with the key."""
    return xor_encrypt(encrypted_data, key)


def encrypt_token_new(token: str) -> str:
    """Encrypt a token and return as a base64 encoded string (NEW - without key storage)."""
    encrypted = xor_encrypt(token.encode(), ENCRYPTION_KEY.encode())
    return base64.b64encode(encrypted).decode()


def decrypt_token_old(encrypted_token: str) -> str:
    """Decrypt a base64 encoded encrypted token (OLD - with key extraction)."""
    decoded = base64.b64decode(encrypted_token)
    encrypted_data = decoded[len(ENCRYPTION_KEY.encode()) :]
    decrypted = xor_decrypt(encrypted_data, ENCRYPTION_KEY.encode())
    return decrypted.decode()


def encrypt_token_old(token: str) -> str:
    """Encrypt a token and return as a base64 encoded string (OLD - with key storage)."""
    encrypted = xor_encrypt(token.encode(), ENCRYPTION_KEY.encode())
    return base64.b64encode(ENCRYPTION_KEY.encode() + encrypted).decode()


def decrypt_token_new(encrypted_token: str) -> str:
    """Decrypt a base64 encoded encrypted token (NEW - without key extraction)."""
    decoded = base64.b64decode(encrypted_token)
    decrypted = xor_decrypt(decoded, ENCRYPTION_KEY.encode())
    return decrypted.decode()


def upgrade() -> None:
    """Migrate tokens from old format (with embedded key) to new format (without key)."""

    bots = sa.table(
        'bots',
        sa.column('id', sa.Integer),
        sa.column('username', sa.String),
        sa.column('user_id', sa.BigInteger),
        sa.column('token', sa.String),
    )

    connection = op.get_bind()
    bot_records = list(connection.execute(bots.select()))
    logger.info(f'Found {len(bot_records)} bots to migrate')

    migrated_count = 0
    failed_count = 0

    for bot in bot_records:
        try:
            decrypted_token = decrypt_token_old(bot.token)
            new_encrypted_token = encrypt_token_new(decrypted_token)
            connection.execute(
                bots.update().where(bots.c.id == bot.id).values(token=new_encrypted_token)
            )
            logger.info(f'✓ Migrated bot {bot.username} (ID: {bot.user_id})')
            migrated_count += 1

        except Exception as e:  # noqa: BLE001
            logger.error(f'✗ Failed to migrate bot {bot.username} (ID: {bot.user_id}): {e}')
            failed_count += 1

    logger.info(f'Migration completed: {migrated_count} successful, {failed_count} failed')


def downgrade() -> None:
    """Migrate tokens back from new format (without key) to old format (with embedded key)."""

    # Create a temp table reference
    bots = sa.table(
        'bots',
        sa.column('id', sa.Integer),
        sa.column('username', sa.String),
        sa.column('user_id', sa.BigInteger),
        sa.column('token', sa.String),
    )

    connection = op.get_bind()
    bot_records = list(connection.execute(bots.select()))
    logger.info(f'Found {len(bot_records)} bots to rollback')

    migrated_count = 0
    failed_count = 0

    for bot in bot_records:
        try:
            decrypted_token = decrypt_token_new(bot.token)
            old_encrypted_token = encrypt_token_old(decrypted_token)
            connection.execute(
                bots.update().where(bots.c.id == bot.id).values(token=old_encrypted_token)
            )

            logger.info(f'✓ Rolled back bot {bot.username} (ID: {bot.user_id})')
            migrated_count += 1

        except Exception as e:  # noqa: BLE001
            logger.error(f'✗ Failed to rollback bot {bot.username} (ID: {bot.user_id}): {e}')
            failed_count += 1

    logger.info(f'Rollback completed: {migrated_count} successful, {failed_count} failed')
