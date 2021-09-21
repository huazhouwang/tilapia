from pycoin.ecdsa.secp256k1 import secp256k1_generator
from pycoin.key.Key import Key as PycoinKey

from tilapia.lib.secret.keys.base import BaseECDSAKey


class ECDSASecp256k1(BaseECDSAKey):
    pycoin_key: PycoinKey = PycoinKey.make_subclass(symbol=None, network=None, generator=secp256k1_generator)
