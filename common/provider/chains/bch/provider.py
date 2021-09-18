import itertools
import logging
from typing import Dict, Tuple

from common.basic import bip44
from common.basic.functional.require import require
from common.hardware import interfaces as hardware_interfaces
from common.provider import data
from common.provider.chains import btc
from common.provider.chains.bch.sdk import cash_address
from common.secret import interfaces as secret_interfaces

logger = logging.getLogger("app.chain")


class BCHProvider(btc.BTCProvider):
    ADDRESS_PREFIX = "bitcoincash"

    def pubkey_to_address(self, verifier: secret_interfaces.VerifierInterface, encoding: str = None) -> str:
        require(encoding == "P2PKH", f"Invalid address encoding: {encoding}")

        pubkey = verifier.get_pubkey(compressed=True)
        pubkey_hash = self.network.keys.public(pubkey).hash160(is_compressed=True)

        if encoding == "P2PKH":  # Pay To Public Key Hash
            address = cash_address.to_cash_address(self.ADDRESS_PREFIX, pubkey_hash)
        else:
            raise Exception("Should not be here")

        return address

    def verify_address(self, address: str) -> data.AddressValidation:
        is_valid, encoding = False, None

        try:
            if ":" not in address:
                address = f"{self.ADDRESS_PREFIX}:{address}"

            prefix, _ = address.split(":")
            if prefix == self.ADDRESS_PREFIX:
                is_valid = cash_address.is_valid_cash_address(address)
                encoding = "P2PKH" if is_valid else None
        except Exception as e:
            logger.exception(f"Illegal address: {address}, error: {e}")

        address = address if is_valid else ""

        return data.AddressValidation(
            normalized_address=address,
            display_address=address,
            is_valid=is_valid,
            encoding=encoding,
        )

    def _cash_address_to_legacy_address(self, address: str) -> str:
        if ":" not in address:
            return address

        pubkey_hash = cash_address.export_pubkey_hash(address)
        return self.network.address.for_p2pkh(pubkey_hash)

    def _pre_process_unsigned_tx(self, unsigned_tx: data.UnsignedTx, signers: dict) -> Tuple[data.UnsignedTx, dict]:
        for i in itertools.chain(unsigned_tx.inputs, unsigned_tx.outputs):
            i.address = self._cash_address_to_legacy_address(i.address)  # pycoin supports legacy bch address only

        signers = {self._cash_address_to_legacy_address(k): v for k, v in signers.items()}

        return unsigned_tx, signers

    def sign_transaction(
        self, unsigned_tx: data.UnsignedTx, signers: Dict[str, secret_interfaces.SignerInterface]
    ) -> data.SignedTx:
        unsigned_tx, signers = self._pre_process_unsigned_tx(unsigned_tx, signers)
        return super(BCHProvider, self).sign_transaction(unsigned_tx, signers)

    def hardware_sign_transaction(
        self,
        hardware_client: hardware_interfaces.HardwareClientInterface,
        unsigned_tx: data.UnsignedTx,
        bip44_path_of_signers: Dict[str, bip44.BIP44Path],
    ) -> data.SignedTx:
        unsigned_tx, bip44_path_of_signers = self._pre_process_unsigned_tx(unsigned_tx, bip44_path_of_signers)
        return super(BCHProvider, self).hardware_sign_transaction(hardware_client, unsigned_tx, bip44_path_of_signers)

    def get_token_info_by_address(self, token_address: str) -> Tuple[str, str, int]:
        raise NotImplementedError()
