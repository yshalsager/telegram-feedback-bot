import hashlib
import hmac
from functools import lru_cache
from typing import cast

from cryptography.fernet import Fernet
from django.conf import settings

fernet_telegram = Fernet(settings.TELEGRAM_ENCRYPTION_KEY.encode())


@lru_cache
def encrypt_token(token: str, encryptor: Fernet = fernet_telegram) -> str:
    """
    Encrypt a token using Fernet for production-grade security.
    """
    if not token:
        return ''
    encrypted_bytes = encryptor.encrypt(token.encode())
    return cast(str, encrypted_bytes.decode())


@lru_cache
def decrypt_token(encrypted_token: str, decryptor: Fernet = fernet_telegram) -> str:
    """
    Decrypt a Fernet-encrypted token.
    """
    if not encrypted_token:
        return ''
    decrypted_bytes = decryptor.decrypt(encrypted_token.encode())
    return cast(str, decrypted_bytes.decode())


@lru_cache
def generate_bot_webhook_secret(bot_uuid: str) -> str:
    """
    Generate a unique, deterministic secret for a bot using HMAC-SHA256.

    :param bot_uuid: The bot's UUID string

    :return: Base64-encoded HMAC-SHA256 hash
    """
    if not bot_uuid or not settings.SECRET_KEY:
        return ''

    secret = hmac.new(
        key=settings.SECRET_KEY.encode(), msg=bot_uuid.encode(), digestmod=hashlib.sha256
    )

    return secret.hexdigest()


@lru_cache
def verify_bot_webhook_secret(bot_uuid: str, provided_secret: str) -> bool:
    """
    Verify a bot's webhook secret by recalculating the HMAC.

    :param bot_uuid: The bot's UUID
    :param provided_secret: The secret to verify

    :return: True if the secret is valid
    """
    expected_secret = generate_bot_webhook_secret(bot_uuid)
    return hmac.compare_digest(expected_secret, provided_secret)
