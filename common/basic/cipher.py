import base64
import hashlib
import os

import pyaes

try:
    from cryptography.hazmat.backends import default_backend as CG_default_backend
    from cryptography.hazmat.primitives.ciphers import Cipher as CG_Cipher
    from cryptography.hazmat.primitives.ciphers import algorithms as CG_algorithms
    from cryptography.hazmat.primitives.ciphers import modes as CG_modes

    HAS_CRYPTOGRAPHY = True
except Exception as e:  # noqa
    HAS_CRYPTOGRAPHY = False


class InvalidPassword(Exception):
    pass


def _padding(data: bytes) -> bytes:
    pad_size = 16 - (len(data) % 16)
    return data + bytes([pad_size]) * pad_size


def _strip_padding(data: bytes) -> bytes:
    if not data or len(data) % 16 != 0:
        raise ValueError("Invalid length")

    pad_size = data[-1]
    if not (0 < pad_size <= 16):
        raise ValueError("Invalid pad size (out of range)")
    for i in data[-pad_size:]:
        if i != pad_size:
            raise ValueError("Invalid padding byte (inconsistent)")

    return data[:-pad_size]


def _aes_encrypt_with_iv(secret: bytes, iv: bytes, data: bytes) -> bytes:
    data = _padding(data)

    if HAS_CRYPTOGRAPHY:
        cipher = CG_Cipher(CG_algorithms.AES(secret), CG_modes.CBC(iv), backend=CG_default_backend())
        encryptor = cipher.encryptor()
        cypher = encryptor.update(data) + encryptor.finalize()
    else:
        aes_cbc = pyaes.AESModeOfOperationCBC(secret, iv=iv)
        encryptor = pyaes.Encrypter(aes_cbc, padding=pyaes.PADDING_NONE)
        cypher = encryptor.feed(data) + encryptor.feed()  # empty aes.feed() flushes buffer

    return cypher


def _aes_decrypt_with_iv(secret: bytes, iv: bytes, data: bytes) -> bytes:
    if HAS_CRYPTOGRAPHY:
        cipher = CG_Cipher(CG_algorithms.AES(secret), CG_modes.CBC(iv), backend=CG_default_backend())
        decryptor = cipher.decryptor()
        data = decryptor.update(data) + decryptor.finalize()
    else:
        cipher = pyaes.AESModeOfOperationCBC(secret, iv=iv)
        decryptor = pyaes.Decrypter(cipher, padding=pyaes.PADDING_NONE)
        data = decryptor.feed(data) + decryptor.feed()  # empty aes.feed() flushes buffer

    try:
        return _strip_padding(data)
    except ValueError as e:
        raise InvalidPassword from e


def _hash_password(password: str) -> bytes:
    return hashlib.sha256(hashlib.sha256(password.encode()).digest()).digest()


def encrypt(password: str, plaintext: str) -> str:
    secret = _hash_password(password)
    iv = bytes(os.urandom(16))
    ct = _aes_encrypt_with_iv(secret, iv, plaintext.encode())
    return base64.b64encode(iv + ct).decode()


def decrypt(password: str, ciphertext: str) -> str:
    secret = _hash_password(password)
    buffer = base64.b64decode(ciphertext)
    iv, ct = buffer[:16], buffer[16:]
    return _aes_decrypt_with_iv(secret, iv, ct).decode()
