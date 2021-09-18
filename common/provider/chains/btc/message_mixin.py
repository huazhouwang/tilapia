import abc
import binascii
import logging
from typing import Any

from pycoin import intbytes as pycoin_intbytes
from pycoin.encoding import bytes32 as pycoin_bytes32
from pycoin.encoding import sec as pycoin_sec

from common.basic.functional.require import require
from common.basic.functional.wraps import error_interrupter
from common.provider import data, interfaces
from common.secret import data as secret_data
from common.secret import interfaces as secret_interfaces
from common.secret.keys.base import BaseECDSAKey
from common.secret.registry import key_class_on_curve

logger = logging.getLogger("app.chain")


class BTCMessageMixin(interfaces.MessageSupportingMixin, abc.ABC):
    @property
    @abc.abstractmethod
    def network(self) -> Any:
        pass

    @abc.abstractmethod
    def pubkey_to_address(self, verifier: secret_interfaces.VerifierInterface, encoding: str = None) -> str:
        pass

    @abc.abstractmethod
    def verify_address(self, address: str) -> data.AddressValidation:
        pass

    def sign_message(
        self, message: str, signer: secret_interfaces.SignerInterface, address: str = None, **kwargs
    ) -> str:
        require(address, "Address is required to sign the message")

        validation = self.verify_address(address)
        require(validation.is_valid, f"Invalid address: {address}")

        message_hash = pycoin_bytes32.to_bytes_32(self.network.msg.hash_for_signing(message))
        sig, rec_id = signer.sign(message_hash)
        flag = 27 + rec_id

        if validation.encoding == "P2PKH":
            flag += 4
        elif validation.encoding == "P2WPKH-P2SH":
            flag += 8
        elif validation.encoding == "P2WPKH":
            flag += 8 + 4

        # noinspection PyTypeChecker
        signature = binascii.b2a_base64(pycoin_intbytes.int2byte(flag) + sig).strip().decode()
        return signature

    @error_interrupter(logger, interrupt=True, default=False)
    def verify_message(self, address: str, message: str, signature: str) -> bool:
        validation = self.verify_address(address)
        require(validation.is_valid, f"Invalid address: {address}")

        compressed, address_encoding, rec_id, sig = _decode_signature(signature)
        if not compressed:
            raise ValueError("Only compressed pubkey supported")
        elif address_encoding != validation.encoding:
            raise ValueError("Address encoding not match")

        message_hash = self.network.msg.hash_for_signing(message)
        pubkey_pair = _pair_for_message_hash(self.network, message_hash, rec_id, sig)
        pubkey_bytes = pycoin_sec.public_pair_to_sec(pubkey_pair)

        curve_cls = key_class_on_curve(secret_data.CurveEnum.SECP256K1)
        assert issubclass(curve_cls, BaseECDSAKey)
        verifier = curve_cls(pubkey=pubkey_bytes)
        recovered_address = self.pubkey_to_address(verifier, address_encoding)

        return recovered_address == address


def _decode_signature(signature: str):
    # Refer to bitcoinjs-message/index.js/decodeSignature

    buffer = binascii.a2b_base64(signature)

    if len(buffer) != 65:
        raise ValueError("Wrong length, expected 65")

    flag = buffer[0] - 27
    if flag < 0 or flag > 15:
        raise ValueError("First byte out of range")

    compressed = bool(flag & 12)
    encoding = "P2PKH" if not (flag & 8) else ("P2WPKH-P2SH" if not (flag & 4) else "P2WPKH")

    return compressed, encoding, (flag & 3), buffer[1:]


def _pair_for_message_hash(network, message_hash: bytes, rec_id: int, sig: bytes):
    generator = network.generator
    y_parity = rec_id & 1
    r, s = pycoin_bytes32.from_bytes_32(sig[:32]), pycoin_bytes32.from_bytes_32(sig[32:])

    q = generator.possible_public_pairs_for_signature(
        message_hash,
        (r, s),
        y_parity=y_parity,
    )[0]

    if rec_id > 1:
        order = generator.order()
        q = generator.Point(q[0] + order, q[1])

    return q
