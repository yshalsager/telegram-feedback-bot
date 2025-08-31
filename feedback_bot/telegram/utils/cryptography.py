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
