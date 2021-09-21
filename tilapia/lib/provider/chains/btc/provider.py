import itertools
import logging
from typing import Any, Dict, Set, Tuple

from pycoin.coins.bitcoin import Tx as pycoin_tx

from tilapia.lib.basic.functional.require import require
from tilapia.lib.coin import data as coin_data
from tilapia.lib.conf import settings
from tilapia.lib.provider import data, interfaces
from tilapia.lib.provider.chains.btc import hardware_mixin, message_mixin
from tilapia.lib.provider.chains.btc.clients import blockbook
from tilapia.lib.provider.chains.btc.sdk import network, transaction
from tilapia.lib.secret import interfaces as secret_interfaces

logger = logging.getLogger("app.chain")


class BTCProvider(interfaces.ProviderInterface, hardware_mixin.BTCHardwareMixin, message_mixin.BTCMessageMixin):
    def __init__(self, chain_info: coin_data.ChainInfo, *args, **kwargs):
        super(BTCProvider, self).__init__(chain_info, *args, **kwargs)
        self._network = None
        self._tx_version = None
        self._tx_op_return_size_limit = None
        self._supported_encodings = None

    @property
    def network(self) -> Any:
        if self._network is None:
            self._network = network.get_network_by_chain_code(self.chain_info.chain_code)

        return self._network

    @property
    def tx_version(self) -> int:
        if self._tx_version is None:
            self._tx_version = transaction.TX_VERSION

        return self._tx_version

    @property
    def tx_op_return_size_limit(self) -> int:
        if self._tx_op_return_size_limit is None:
            self._tx_op_return_size_limit = transaction.TX_OP_RETURN_SIZE_LIMIT

        return self._tx_op_return_size_limit

    @property
    def supported_encodings(self) -> Set[str]:
        if self._supported_encodings is None:
            self._supported_encodings = {
                *self.chain_info.bip44_purpose_options.keys(),
                self.chain_info.default_address_encoding,
            }
        return self._supported_encodings

    @property
    def client(self) -> blockbook.BlockBook:
        return self.client_selector(instance_required=blockbook.BlockBook)

    def verify_address(self, address: str) -> data.AddressValidation:
        is_valid, encoding = False, None

        try:
            parsed_address = self.network.parse.address(address)
            address_info = parsed_address.info() if parsed_address else {}

            address_type = address_info.get("type")
            if address_type == "p2pkh":
                encoding = "P2PKH"
            elif address_type == "p2pkh_wit":
                encoding = "P2WPKH"
            elif address_type == "p2sh":
                encoding = "P2WPKH-P2SH"  # Cannot distinguish between legacy P2SH and P2WPKH-P2SH

            is_valid = encoding is not None and encoding in self.supported_encodings
            encoding = encoding if is_valid else None
        except Exception as e:
            logger.exception(f"Illegal address: {address}, error: {e}")

        address = address if is_valid else ""

        return data.AddressValidation(
            normalized_address=address,
            display_address=address,
            is_valid=is_valid,
            encoding=encoding,
        )

    def pubkey_to_address(self, verifier: secret_interfaces.VerifierInterface, encoding: str = None) -> str:
        require(encoding in self.supported_encodings, f"Invalid address encoding: {encoding}")

        pubkey = verifier.get_pubkey(compressed=True)
        pubkey_hash = self.network.keys.public(pubkey).hash160(is_compressed=True)

        if encoding == "P2PKH":  # Pay To Public Key Hash
            address = self.network.address.for_p2pkh(pubkey_hash)
        elif encoding == "P2WPKH":  # Pay To Witness Public Key Hash
            address = self.network.address.for_p2pkh_wit(pubkey_hash)
        elif encoding == "P2WPKH-P2SH":  # P2WPKH nested in BIP16 P2SH
            witness_script = self.network.contract.for_p2pkh_wit(pubkey_hash)
            address = self.network.address.for_p2s(witness_script)
        else:
            raise Exception("Should not be here")

        return address

    def fill_unsigned_tx(self, unsigned_tx: data.UnsignedTx) -> data.UnsignedTx:
        fee_price_per_unit = unsigned_tx.fee_price_per_unit or int(
            self.client.get_prices_per_unit_of_fee().normal.price
        )
        fee_limit = unsigned_tx.fee_limit or 0

        if unsigned_tx.inputs and unsigned_tx.outputs:
            input_validations = [self.verify_address(i.address) for i in unsigned_tx.inputs]
            output_validations = [self.verify_address(i.address) for i in unsigned_tx.outputs]
            if all(i.is_valid for i in itertools.chain(input_validations, output_validations)):
                vsize = transaction.calculate_vsize(
                    input_encodings=[i.encoding for i in input_validations],
                    output_encodings=[i.encoding for i in output_validations],
                    op_return=unsigned_tx.payload.get("op_return"),
                    op_return_size_limit=self.tx_op_return_size_limit,
                )
                fee_limit = max(fee_limit, vsize)

        fee_limit = fee_limit or transaction.PLACEHOLDER_VSIZE

        return unsigned_tx.clone(
            fee_limit=fee_limit,
            fee_price_per_unit=fee_price_per_unit,
        )

    def sign_transaction(
        self, unsigned_tx: data.UnsignedTx, signers: Dict[str, secret_interfaces.SignerInterface]
    ) -> data.SignedTx:
        tx = transaction.create_pycoin_tx(
            self.network,
            unsigned_tx,
            version=self.tx_version,
            op_return_size_limit=self.tx_op_return_size_limit,
        )
        tx.check()

        tx.sign(
            hash160_lookup=transaction.build_hash160_lookup(self.network, signers.values()),
            p2sh_lookup=transaction.build_p2sh_lookup(self.network, signers.values()),
        )
        self._check_tx_after_signed(tx)

        return data.SignedTx(
            txid=tx.id(),
            raw_tx=tx.as_hex(),
        )

    def _check_tx_after_signed(self, tx: pycoin_tx.Tx):
        unsigned_after = tx.bad_solution_count()
        if unsigned_after > 0:
            not_fully_signed_message = (
                f"{unsigned_after} TxIn items still unsigned, tx: {tx.as_hex(include_unspents=True)}"
            )
            if settings.IS_DEV:
                dump_message = transaction.debug_dump_tx(self.network, tx)
                logger.error("\n".join((not_fully_signed_message, dump_message)))
            raise Exception(not_fully_signed_message)

    def get_token_info_by_address(self, token_address: str) -> Tuple[str, str, int]:
        raise NotImplementedError()
