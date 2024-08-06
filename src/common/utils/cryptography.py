import base64

from src import ENCRYPTION_KEY


def xor_encrypt(data: bytes, key: bytes) -> bytes:
    """Encrypt data using XOR with the key."""
    return bytes(
        a ^ b for a, b in zip(data, (key * (len(data) // len(key) + 1))[: len(data)], strict=False)
    )


def xor_decrypt(encrypted_data: bytes, key: bytes) -> bytes:
    """Decrypt data using XOR with the key."""
    return xor_encrypt(encrypted_data, key)  # XOR encryption is its own inverse


def encrypt_token(token: str) -> str:
    """Encrypt a token and return as a base64 encoded string."""
    if not ENCRYPTION_KEY:
        raise ValueError(
            'ENCRYPTION_KEY is not set, '
            'generate it with `python -c "from secrets import token_bytes; print(token_bytes(32).hex())"`'
        )
    encrypted = xor_encrypt(token.encode(), ENCRYPTION_KEY.encode())
    # Combine key and encrypted data, then base64 encode
    return base64.b64encode(ENCRYPTION_KEY.encode() + encrypted).decode()


def decrypt_token(encrypted_token: str) -> str:
    """Decrypt a base64 encoded encrypted token."""
    decoded = base64.b64decode(encrypted_token)
    key, encrypted = decoded[:32], decoded[32:]
    decrypted = xor_decrypt(encrypted, key)
    return decrypted.decode()
