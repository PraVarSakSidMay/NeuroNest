"""AES-256-GCM encryption with HKDF-SHA256 key derivation per user."""
import base64, os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from app.config import get_settings

settings = get_settings()
NONCE_SIZE = 12
KEY_SIZE = 32


def _derive_key(user_id: str) -> bytes:
    master_key = settings.secret_key.encode("utf-8")
    hkdf = HKDF(algorithm=hashes.SHA256(), length=KEY_SIZE, salt=None, info=f"neuronest-chat-{user_id}".encode("utf-8"))
    return hkdf.derive(master_key)


def encrypt(plaintext: str, user_id: str) -> str:
    key = _derive_key(user_id)
    aesgcm = AESGCM(key)
    nonce = os.urandom(NONCE_SIZE)
    ciphertext_with_tag = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return base64.b64encode(nonce + ciphertext_with_tag).decode("utf-8")


def decrypt(encrypted_b64: str, user_id: str) -> str:
    try:
        key = _derive_key(user_id)
        aesgcm = AESGCM(key)
        encrypted_bytes = base64.b64decode(encrypted_b64.encode("utf-8"))
        nonce = encrypted_bytes[:NONCE_SIZE]
        ciphertext_with_tag = encrypted_bytes[NONCE_SIZE:]
        return aesgcm.decrypt(nonce, ciphertext_with_tag, None).decode("utf-8")
    except Exception as e:
        raise ValueError(f"Decryption failed: {e}")


def is_encrypted(value: str) -> bool:
    try:
        decoded = base64.b64decode(value.encode("utf-8"))
        return len(decoded) >= NONCE_SIZE + 16
    except Exception:
        return False
