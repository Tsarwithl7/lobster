import os

from argon2.low_level import Type, hash_secret_raw
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

_KEY_LEN = 32
_NONCE_LEN = 12
_SALT_LEN = 16


def _derive_key(passphrase: str, salt: bytes) -> bytes:
    return hash_secret_raw(
        secret=passphrase.encode(),
        salt=salt,
        time_cost=3,
        memory_cost=64 * 1024,
        parallelism=4,
        hash_len=_KEY_LEN,
        type=Type.ID,
    )


def encrypt(plaintext: bytes, passphrase: str) -> bytes:
    salt = os.urandom(_SALT_LEN)
    nonce = os.urandom(_NONCE_LEN)
    key = _derive_key(passphrase, salt)
    ct = AESGCM(key).encrypt(nonce, plaintext, None)
    return salt + nonce + ct


def decrypt(blob: bytes, passphrase: str) -> bytes:
    salt = blob[:_SALT_LEN]
    nonce = blob[_SALT_LEN : _SALT_LEN + _NONCE_LEN]
    ct = blob[_SALT_LEN + _NONCE_LEN :]
    key = _derive_key(passphrase, salt)
    return AESGCM(key).decrypt(nonce, ct, None)
