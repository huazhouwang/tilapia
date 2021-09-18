import abc

import ecdsa.keys
from pycoin.encoding import bytes32 as pycoin_bytes32

from common.provider import interfaces
from common.provider.chains.eth.sdk import message as message_sdk
from common.provider.chains.eth.sdk import utils
from common.secret import data as secret_data
from common.secret import interfaces as secret_interfaces
from common.secret.keys.base import BaseECDSAKey
from common.secret.registry import key_class_on_curve


class ETHMessageMixin(interfaces.MessageSupportingMixin, abc.ABC):
    @abc.abstractmethod
    def pubkey_to_address(self, verifier: secret_interfaces.VerifierInterface, encoding: str = None) -> str:
        pass

    def sign_message(self, message: str, signer: secret_interfaces.SignerInterface, **kwargs) -> str:
        message_hash = message_sdk.hash_message(message)
        sig, rec_id = signer.sign(message_hash)
        v = rec_id + 27
        sig += bytes([v])
        return utils.add_0x_prefix(sig.hex())

    def verify_message(self, address: str, message: str, signature: str) -> bool:
        recovered_address = self.ec_recover(message, signature)
        return recovered_address == address

    def ec_recover(self, message: str, signature: str) -> str:
        digest = message_sdk.hash_message(message)
        signature = bytes.fromhex(utils.remove_0x_prefix(signature))
        r, s, v = signature[:32], signature[32:64], signature[64]

        pubkey = _recover_public_key(
            pycoin_bytes32.from_bytes_32(digest),
            pycoin_bytes32.from_bytes_32(r),
            pycoin_bytes32.from_bytes_32(s),
            v - 27,
        )

        curve_cls = key_class_on_curve(secret_data.CurveEnum.SECP256K1)
        assert issubclass(curve_cls, BaseECDSAKey)
        verifier = curve_cls.from_key(pubkey=pubkey)
        return self.pubkey_to_address(verifier)


def _recover_public_key(digest: int, r: int, s: int, recid: int) -> bytes:
    curve = ecdsa.curves.SECP256k1
    curve_fp = curve.curve
    n = curve.order
    e = digest
    x = r + (recid // 2) * n

    alpha = (pow(x, 3, curve_fp.p()) + (curve_fp.a() * x) + curve_fp.b()) % curve_fp.p()
    beta = ecdsa.numbertheory.square_root_mod_prime(alpha, curve_fp.p())
    y = beta if (beta - recid) % 2 == 0 else curve_fp.p() - beta

    generator = ecdsa.ellipticcurve.PointJacobi(curve_fp, x, y, 1, n)
    point = ecdsa.numbertheory.inverse_mod(r, n) * (s * generator + (-e % n) * curve.generator)
    verifying_key = ecdsa.VerifyingKey.from_public_point(point, curve, hashfunc=None)
    return verifying_key.to_string("compressed")
