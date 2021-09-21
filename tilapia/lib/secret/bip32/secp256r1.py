from tilapia.lib.secret.bip32.base import BaseBIP32ECDSA
from tilapia.lib.secret.keys.secp256r1 import ECDSASecp256r1


class BIP32Secp256r1(BaseBIP32ECDSA):
    bip32_salt = b"Nist256p1 seed"
    key_class = ECDSASecp256r1
