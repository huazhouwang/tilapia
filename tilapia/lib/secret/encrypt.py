from tilapia.lib.basic import cipher
from tilapia.lib.basic.functional.require import require


def encrypt_data(password: str, data: str) -> str:
    require(bool(password))
    return cipher.encrypt(password, data)


def decrypt_data(password: str, data: str) -> str:
    require(bool(password))
    return cipher.decrypt(password, data)
