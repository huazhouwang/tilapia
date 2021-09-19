import hmac
from typing import List

from mnemonic import Mnemonic
from pycoin.encoding import b58 as pycoin_b58
from pycoin.encoding import hash as pycoin_hash

from wallet.lib.basic import bip32
from wallet.lib.basic.functional.require import require


def encode_base58_check(value: bytes) -> str:
    return pycoin_b58.b2a_hashed_base58(value)


def decode_base58_check(value: str) -> bytes:
    return pycoin_b58.a2b_hashed_base58(value)


def hmac_oneshot(key: bytes, msg: bytes, digest) -> bytes:
    return hmac.HMAC(key, msg, digest).digest()


def decode_bip32_path(path: str) -> List[int]:
    return bip32.decode_bip44_path(path)


def encode_bip32_path(path_as_ints: List[int]) -> str:
    return bip32.encode_bip32_path(path_as_ints)


def hash_160(digest: bytes) -> bytes:
    return pycoin_hash.hash160(digest)


def merge_bip32_paths(*paths: str) -> str:
    nodes = ["m"]
    paths = (i for i in paths if i)
    for path in paths:
        sub_nodes = path.split("/")
        sub_nodes = (i for i in sub_nodes if i and i.lower() != "m")
        nodes.extend(sub_nodes)

    return "/".join(nodes)


def diff_bip32_paths(src: str, dst: str) -> str:
    require(src.startswith("m") and dst.startswith("m") and dst.startswith(src))
    return "m" + dst[len(src) :]


def mnemonic_to_seed(mnemonic: str, passphrase: str = None) -> bytes:
    return Mnemonic.to_seed(mnemonic, passphrase=passphrase or "")


def generate_mnemonic(strength: int) -> str:
    return Mnemonic("english").generate(strength)


def check_mnemonic(mnemonic: str) -> bool:
    return Mnemonic("english").check(mnemonic)
