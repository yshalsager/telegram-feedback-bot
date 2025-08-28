from typing import cast

from cryptography.fernet import Fernet
from django.conf import settings

_fernet = Fernet(settings.TELEGRAM_ENCRYPTION_KEY.encode())


def encrypt_token(token: str) -> str:
    """
    Encrypt a token using Fernet for production-grade security.
    """
    if not token:
        return ''
    encrypted_bytes = _fernet.encrypt(token.encode())
    return cast(str, encrypted_bytes.decode())


def decrypt_token(encrypted_token: str) -> str:
    """
    Decrypt a Fernet-encrypted token.
    """
    if not encrypted_token:
        return ''
    decrypted_bytes = _fernet.decrypt(encrypted_token.encode())
    return cast(str, decrypted_bytes.decode())
