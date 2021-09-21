from typing import Type

from tilapia.lib.basic.functional.require import require
from tilapia.lib.secret.bip32 import ed25519 as bip32_ed25519
from tilapia.lib.secret.bip32 import secp256k1 as bip32_secp256k1
from tilapia.lib.secret.bip32 import secp256r1 as bip32_secp256r1
from tilapia.lib.secret.data import CurveEnum
from tilapia.lib.secret.interfaces import BIP32Interface, KeyInterface
from tilapia.lib.secret.keys import ed25519 as key_ed25519
from tilapia.lib.secret.keys import secp256k1 as key_secp256k1
from tilapia.lib.secret.keys import secp256r1 as key_secp256r1

KEY_CLASS_MAPPING = {
    CurveEnum.SECP256K1: key_secp256k1.ECDSASecp256k1,
    CurveEnum.SECP256R1: key_secp256r1.ECDSASecp256r1,
    CurveEnum.ED25519: key_ed25519.ED25519,
}


def key_class_on_curve(curve: CurveEnum) -> Type[KeyInterface]:
    require(curve in KEY_CLASS_MAPPING, f"{curve} unsupported")
    return KEY_CLASS_MAPPING[curve]


BIP32_CLASS_MAPPING = {
    CurveEnum.SECP256K1: bip32_secp256k1.BIP32Secp256k1,
    CurveEnum.SECP256R1: bip32_secp256r1.BIP32Secp256r1,
    CurveEnum.ED25519: bip32_ed25519.BIP32ED25519,
}


def bip32_class_on_curve(curve: CurveEnum) -> Type[BIP32Interface]:
    require(curve in BIP32_CLASS_MAPPING, f"{curve} unsupported")
    return BIP32_CLASS_MAPPING[curve]
