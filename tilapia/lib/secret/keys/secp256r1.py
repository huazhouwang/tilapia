from pycoin.ecdsa.secp256r1 import secp256r1_generator
from pycoin.key.Key import Key as PycoinKey

from tilapia.lib.secret.keys.base import BaseECDSAKey


class ECDSASecp256r1(BaseECDSAKey):
    pycoin_key: PycoinKey = PycoinKey.make_subclass(symbol=None, network=None, generator=secp256r1_generator)
