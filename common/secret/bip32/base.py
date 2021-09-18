import hashlib
import struct
from abc import ABC

from pycoin.encoding import bytes32 as pycoin_bytes32
from pycoin.encoding import sec as pycoin_sec
from pycoin.key import bip32 as pycoin_bip32

from common.basic.functional.require import require
from common.secret import utils
from common.secret.interfaces import BIP32Interface


def extract_hwif_data(data: bytes):
    depth = ord(data[4:5])
    parent_fingerprint, child_index = struct.unpack(">4sL", data[5:13])
    chaincode = data[13:45]
    is_private = data[45:46] == b"\0"
    key_data = data[45:]

    return depth, parent_fingerprint, child_index, chaincode, is_private, key_data


class BaseBIP32ECDSA(BIP32Interface, ABC):
    @classmethod
    def get_generator(cls):
        pycoin_key = getattr(cls.key_class, "pycoin_key")
        require(pycoin_key is not None)
        # noinspection PyProtectedMember
        return pycoin_key._generator

    @classmethod
    def from_master_seed(cls, master_seed: bytes) -> "BIP32Interface":
        require(cls.bip32_salt is not None)
        require(cls.key_class is not None)

        while True:
            i_64 = utils.hmac_oneshot(key=cls.bip32_salt, msg=master_seed, digest=hashlib.sha512)
            prvkey, chain_code = i_64[:32], i_64[32:]
            prvkey_as_number = pycoin_bytes32.from_bytes_32(prvkey)
            if prvkey_as_number != 0 and prvkey_as_number < cls.get_generator().order():
                break
            else:
                master_seed = i_64

        return cls(prvkey=prvkey, chain_code=chain_code)

    @classmethod
    def deserialize(cls, data: bytes) -> "BIP32Interface":
        depth, parent_fingerprint, child_index, chaincode, is_private, key_data = extract_hwif_data(data)
        if is_private:
            prvkey = key_data[1:]
            pubkey = None
        else:
            prvkey = None
            pubkey = key_data

        return cls(
            prvkey=prvkey,
            pubkey=pubkey,
            chain_code=chaincode,
            depth=depth,
            parent_fingerprint=parent_fingerprint,
            child_index=child_index,
        )

    def _derive(self, child_index: int, is_hardened: bool, as_private: bool) -> "BIP32Interface":
        depth = self.depth + 1
        parent_fingerprint = self.fingerprint

        child_prvkey = None
        child_pubkey = None
        generator = self.get_generator()

        if as_private:
            secret_exponent = pycoin_bytes32.from_bytes_32(self._prvkey)
            child_secret_exponent, child_chain_code = pycoin_bip32.subkey_secret_exponent_chain_code_pair(
                generator,
                secret_exponent,
                self.chain_code,
                child_index,
                is_hardened,
            )
            child_prvkey = pycoin_bytes32.to_bytes_32(child_secret_exponent)
        else:
            pubkey_pair = pycoin_sec.sec_to_public_pair(self._pubkey, generator=generator)
            child_pubkey_pair, child_chain_code = pycoin_bip32.subkey_public_pair_chain_code_pair(
                generator, pubkey_pair, self.chain_code, child_index
            )
            child_pubkey = pycoin_sec.public_pair_to_sec(child_pubkey_pair)

        return self.__class__(
            prvkey=child_prvkey,
            pubkey=child_pubkey,
            chain_code=child_chain_code,
            depth=depth,
            parent_fingerprint=parent_fingerprint,
            child_index=child_index,
        )
