import base64

from src import ENCRYPTION_KEY


def xor_encrypt(data: bytes, key: bytes) -> bytes:
    if isinstance(data, str):  # just in case
        data = data.encode()
    if isinstance(key, str):
        key = key.encode()
    extended_key = (key * ((len(data) // len(key)) + 1))[:len(data)]
    return bytes(a ^ b for a, b in zip(data, extended_key, strict=False))

def encrypt_token(token: str) -> str:
    return base64.b64encode(xor_encrypt(token.encode(), ENCRYPTION_KEY)).decode()

def decrypt_token(encrypted_token: str) -> str:
    return xor_encrypt(base64.b64decode(encrypted_token), ENCRYPTION_KEY).decode()
