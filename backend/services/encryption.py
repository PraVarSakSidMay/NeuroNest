"""
Encryption service for NeuroNest Reflective Journal.

Provides AES-256-GCM field-level encryption with per-user HKDF-SHA256 key
derivation. All sensitive journal fields are encrypted before being written
to the database and decrypted after being read from it.

Ciphertext format (base64-encoded):
    IV (12 bytes) || GCM tag (16 bytes) || ciphertext (variable)

Key derivation:
    HKDF-SHA256(key_material=ENCRYPTION_MASTER_KEY, info=user_id, length=32)

The derived key NEVER leaves this module — it is not stored, logged, or
returned to callers.
"""

import base64
import binascii
import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------


class ConfigurationError(Exception):
    """Raised when a required configuration value (e.g. ENCRYPTION_MASTER_KEY)
    is missing or invalid."""


class DecryptionError(Exception):
    """Raised when decryption fails — either because the GCM authentication
    tag verification failed (tampered ciphertext) or because the wrong
    user_id was supplied (wrong derived key)."""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_ENV_KEY_NAME = "ENCRYPTION_MASTER_KEY"

# Byte layout of the packed ciphertext blob
_IV_LEN = 12   # 96-bit IV required for AES-GCM
_TAG_LEN = 16  # 128-bit GCM authentication tag
_HEADER_LEN = _IV_LEN + _TAG_LEN  # 28 bytes before the actual ciphertext


def _load_master_key() -> bytes:
    """Load and decode the master key from the environment variable.

    Tries base64 decoding first, then hex decoding, then falls back to
    treating the raw string as bytes.  Raises ConfigurationError if the
    variable is absent or empty.
    """
    raw = os.environ.get(_ENV_KEY_NAME, "")
    if not raw:
        raise ConfigurationError(
            f"Environment variable '{_ENV_KEY_NAME}' is absent or empty. "
            "The encryption service cannot start without a master key."
        )

    # 1. Try base64 (standard + URL-safe)
    try:
        decoded = base64.b64decode(raw, validate=True)
        return decoded
    except (binascii.Error, ValueError):
        pass

    # 2. Try hex
    try:
        decoded = bytes.fromhex(raw)
        return decoded
    except ValueError:
        pass

    # 3. Fall back to raw UTF-8 bytes
    return raw.encode("utf-8")


def _derive_user_key(master_key: bytes, user_id: str) -> bytes:
    """Derive a 32-byte per-user AES key using HKDF-SHA256.

    The derived key is returned as raw bytes and must NEVER be stored or
    logged by the caller.

    Args:
        master_key: The raw master key bytes loaded from the environment.
        user_id:    The user's UUID string used as the HKDF ``info`` parameter.

    Returns:
        A 32-byte derived key suitable for AES-256.
    """
    hkdf = HKDF(
        algorithm=SHA256(),
        length=32,
        salt=None,
        info=user_id.encode("utf-8"),
    )
    return hkdf.derive(master_key)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def encrypt_field(plaintext: str, user_id: str) -> str:
    """Encrypt a plaintext string using AES-256-GCM with a per-user derived key.

    A fresh random 12-byte IV is generated for every call, so two calls with
    identical inputs will always produce different ciphertexts.

    The returned value is a base64-encoded blob with the layout:
        IV (12 bytes) || GCM tag (16 bytes) || ciphertext

    Args:
        plaintext: The UTF-8 string to encrypt.  Must be non-empty.
        user_id:   The UUID of the owning user.  Used as the HKDF info
                   parameter to derive a user-specific key.

    Returns:
        A base64-encoded ciphertext string safe for storage in the database.

    Raises:
        ConfigurationError: If ENCRYPTION_MASTER_KEY is absent or empty.
    """
    master_key = _load_master_key()
    derived_key = _derive_user_key(master_key, user_id)

    try:
        iv = os.urandom(_IV_LEN)
        aesgcm = AESGCM(derived_key)

        # AESGCM.encrypt() returns ciphertext || tag (tag appended at the end)
        ct_with_tag = aesgcm.encrypt(iv, plaintext.encode("utf-8"), None)

        # Split: last 16 bytes are the GCM tag; everything before is ciphertext
        ciphertext = ct_with_tag[:-_TAG_LEN]
        tag = ct_with_tag[-_TAG_LEN:]

        # Pack as IV || tag || ciphertext and base64-encode
        packed = iv + tag + ciphertext
        return base64.b64encode(packed).decode("utf-8")
    finally:
        # Ensure the derived key is not kept alive in any local reference
        del derived_key


def decrypt_field(ciphertext_b64: str, user_id: str) -> str:
    """Decrypt a ciphertext produced by :func:`encrypt_field`.

    Args:
        ciphertext_b64: A base64-encoded blob in the format
                        IV (12 bytes) || GCM tag (16 bytes) || ciphertext.
        user_id:        The UUID of the owning user.  Must match the user_id
                        used during encryption; otherwise the GCM tag
                        verification will fail and a DecryptionError is raised.

    Returns:
        The original plaintext string.

    Raises:
        ConfigurationError: If ENCRYPTION_MASTER_KEY is absent or empty.
        DecryptionError:    If the GCM authentication tag verification fails
                            (tampered ciphertext or wrong user_id).
    """
    master_key = _load_master_key()
    derived_key = _derive_user_key(master_key, user_id)

    try:
        try:
            packed = base64.b64decode(ciphertext_b64)
        except (binascii.Error, ValueError) as exc:
            raise DecryptionError(
                "Ciphertext is not valid base64 — data may be corrupted."
            ) from exc

        if len(packed) < _HEADER_LEN:
            raise DecryptionError(
                f"Ciphertext blob is too short ({len(packed)} bytes); "
                f"expected at least {_HEADER_LEN} bytes (IV + tag)."
            )

        iv = packed[:_IV_LEN]
        tag = packed[_IV_LEN:_HEADER_LEN]
        ciphertext = packed[_HEADER_LEN:]

        aesgcm = AESGCM(derived_key)

        # AESGCM.decrypt() expects ciphertext || tag
        ct_with_tag = ciphertext + tag

        try:
            plaintext_bytes = aesgcm.decrypt(iv, ct_with_tag, None)
        except InvalidTag as exc:
            raise DecryptionError(
                "Ciphertext authentication failed — data may be tampered "
                "or the user_id does not match the one used during encryption."
            ) from exc

        return plaintext_bytes.decode("utf-8")
    finally:
        del derived_key
