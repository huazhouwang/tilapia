from abc import ABC
from typing import Optional, Tuple, Type

from pycoin.ecdsa import Generator as PycoinGenerator
from pycoin.encoding import bytes32 as pycoin_bytes32
from pycoin.key.Key import Key as PycoinKey
from pycoin.satoshi import der as pycoin_der

from wallet.lib.basic.functional.require import require
from wallet.lib.secret.interfaces import KeyInterface


class BaseECDSAKey(KeyInterface, ABC):
    pycoin_key: Type[PycoinKey]

    def __init__(self, prvkey: bytes = None, pubkey: bytes = None):
        require(self.pycoin_key is not None, f"Please specify 'pycoin_key' for <{self.__class__}>")
        super(BaseECDSAKey, self).__init__(prvkey=prvkey, pubkey=pubkey)

        self._signing_key: Optional[PycoinKey] = None
        self._verifying_key: Optional[PycoinKey] = None

        if prvkey is not None:
            self._signing_key = self.pycoin_key(pycoin_bytes32.from_bytes_32(prvkey))
            self._verifying_key = self._signing_key.public_copy()
        else:
            require(
                len(pubkey) in (33, 64, 65),
                f"Length of pubkey should be 33, 64 or 65 , but now is {len(pubkey)}",
            )
            self._verifying_key = self.pycoin_key.from_sec(pubkey)

    def has_prvkey(self) -> bool:
        return self._signing_key is not None

    def get_pubkey(self, compressed=True) -> bytes:
        return self._verifying_key.sec(compressed)

    def get_prvkey(self) -> bytes:
        require(self.has_prvkey())
        return pycoin_bytes32.to_bytes_32(self._signing_key.secret_exponent())

    def verify(self, digest: bytes, signature: bytes) -> bool:
        r = pycoin_bytes32.from_bytes_32(signature[:32])
        s = pycoin_bytes32.from_bytes_32(signature[32:])
        return self._verifying_key.verify(digest, pycoin_der.sigencode_der(r, s))

    def sign(self, digest: bytes) -> Tuple[bytes, int]:
        super(BaseECDSAKey, self).sign(digest)

        r, s, rec_id = self.get_generator().sign_with_recid(
            self._signing_key.secret_exponent(), pycoin_bytes32.from_bytes_32(digest)
        )
        signature = pycoin_bytes32.to_bytes_32(r) + pycoin_bytes32.to_bytes_32(s)
        return signature, rec_id

    @classmethod
    def get_generator(cls) -> PycoinGenerator:
        pycoin_key = cls.pycoin_key
        require(pycoin_key is not None)
        # noinspection PyProtectedMember
        return pycoin_key._generator
