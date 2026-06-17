"""
Encryption service using AES-256-GCM with HKDF key derivation.
JWT authentication utilities.
"""

import base64
import os
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import get_settings


security = HTTPBearer()


class EncryptionService:
    """AES-256-GCM encryption service with HKDF-SHA256 key derivation.

    The master key is provided as a base64-encoded string and used to derive
    per-encryption keys via HKDF with a random salt.
    """

    def __init__(self, master_key: str) -> None:
        """Initialize the encryption service.

        Args:
            master_key: A base64-encoded 32-byte master key.
        """
        self._master_key: bytes = base64.b64decode(master_key)

    def _derive_key(self, salt: bytes, info: bytes = b"neuronest-encryption") -> bytes:
        """Derive a 32-byte encryption key from the master key using HKDF-SHA256.

        Args:
            salt: Random salt bytes for key derivation.
            info: Context info for HKDF (default: b"neuronest-encryption").

        Returns:
            A 32-byte derived key.
        """
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            info=info,
        )
        return hkdf.derive(self._master_key)

    def encrypt(self, plaintext: str) -> str:
        """Encrypt a plaintext string using AES-256-GCM.

        Generates a random 16-byte salt and 12-byte IV, derives a key via HKDF,
        and returns the result as base64(salt + iv + ciphertext_with_tag).

        Args:
            plaintext: The string to encrypt.

        Returns:
            A base64-encoded string containing salt + iv + ciphertext.
        """
        salt = os.urandom(16)
        iv = os.urandom(12)
        key = self._derive_key(salt)
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(iv, plaintext.encode("utf-8"), None)
        return base64.b64encode(salt + iv + ciphertext).decode("utf-8")

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt a base64-encoded AES-256-GCM encrypted string.

        Extracts salt (16 bytes), IV (12 bytes), and ciphertext from the
        decoded data, derives the key, and decrypts.

        Args:
            encrypted_data: The base64-encoded encrypted string.

        Returns:
            The decrypted plaintext string.
        """
        raw = base64.b64decode(encrypted_data)
        salt = raw[:16]
        iv = raw[16:28]
        ciphertext = raw[28:]
        key = self._derive_key(salt)
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(iv, ciphertext, None)
        return plaintext.decode("utf-8")


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Get current user ID from JWT token.

    Args:
        credentials: HTTP Bearer token credentials.

    Returns:
        User ID as string.

    Raises:
        HTTPException: 401 if token is invalid or missing.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        settings = get_settings()
        payload = jwt.decode(credentials.credentials, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id: Optional[str] = payload.get("sub") or payload.get("userId")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return str(user_id)
