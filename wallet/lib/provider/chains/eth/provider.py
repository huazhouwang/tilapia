from typing import Dict, Tuple

import eth_abi
import eth_account
import eth_keys

from wallet.lib.basic.functional.require import require
from wallet.lib.provider import data, interfaces
from wallet.lib.provider.chains.eth import Geth, hardware_mixin, message_mixin
from wallet.lib.provider.chains.eth.sdk import utils
from wallet.lib.secret import interfaces as secret_interfaces


class _EthKey(object):
    def __init__(self, signer: secret_interfaces.SignerInterface):
        self.signer = signer

    def sign_msg_hash(self, digest: bytes):
        sig, rec_id = self.signer.sign(digest)
        return eth_keys.keys.Signature(sig + bytes([rec_id]))


class ETHProvider(interfaces.ProviderInterface, hardware_mixin.ETHHardwareMixin, message_mixin.ETHMessageMixin):
    def verify_address(self, address: str) -> data.AddressValidation:
        is_valid = utils.is_address(address)
        normalized_address, display_address = (
            (address.lower(), utils.to_checksum_address(address)) if is_valid else ("", "")
        )
        return data.AddressValidation(
            normalized_address=normalized_address,
            display_address=display_address,
            is_valid=is_valid,
        )

    def pubkey_to_address(self, verifier: secret_interfaces.VerifierInterface, encoding: str = None) -> str:
        pubkey = verifier.get_pubkey(compressed=False)
        address = utils.add_0x_prefix(utils.keccak(pubkey[-64:])[-20:].hex())
        return address

    @property
    def geth(self) -> Geth:
        return self.client_selector(instance_required=Geth)

    def fill_unsigned_tx(self, unsigned_tx: data.UnsignedTx) -> data.UnsignedTx:
        fee_price_per_unit = unsigned_tx.fee_price_per_unit or self.client.get_prices_per_unit_of_fee().normal.price
        nonce = unsigned_tx.nonce
        payload = unsigned_tx.payload.copy()
        tx_input = unsigned_tx.inputs[0] if unsigned_tx.inputs else None
        tx_output = unsigned_tx.outputs[0] if unsigned_tx.outputs else None
        fee_limit = unsigned_tx.fee_limit

        if tx_input is not None and tx_output is not None:
            from_address = tx_input.address
            to_address = tx_output.address
            value = tx_output.value
            token_address = tx_output.token_address

            if nonce is None:
                nonce = self.client.get_address(from_address).nonce

            if token_address is None:
                data = payload.get("data")
            else:
                data = utils.add_0x_prefix(
                    "a9059cbb" + eth_abi.encode_abi(("address", "uint256"), (to_address, value)).hex()
                )  # method_selector(transfer) + byte32_pad(address) + byte32_pad(value)
                value = 0
                to_address = token_address

            if data:
                payload["data"] = data

            if not fee_limit:
                estimate_fee_limit = self.geth.estimate_gas_limit(from_address, to_address, value, data)
                multiplier = self.chain_info.impl_options.get("contract_gaslimit_multiplier", 1.2)
                fee_limit = (
                    round(estimate_fee_limit * multiplier)
                    if token_address or self.geth.is_contract(to_address)
                    else estimate_fee_limit
                )

        fee_limit = fee_limit or 21000

        return unsigned_tx.clone(
            inputs=[tx_input] if tx_input is not None else [],
            outputs=[tx_output] if tx_output is not None else [],
            fee_limit=fee_limit,
            fee_price_per_unit=fee_price_per_unit,
            nonce=nonce,
            payload=payload,
        )

    def sign_transaction(
        self, unsigned_tx: data.UnsignedTx, signers: Dict[str, secret_interfaces.SignerInterface]
    ) -> data.SignedTx:
        require(len(unsigned_tx.inputs) == 1 and len(unsigned_tx.outputs) == 1)
        from_address = unsigned_tx.inputs[0].address
        require(signers.get(from_address) is not None)

        eth_key = _EthKey(signers[from_address])
        tx_dict = self._build_unsigned_tx_dict(unsigned_tx)

        _, _, _, encoded_tx = eth_account.account.sign_transaction_dict(eth_key, tx_dict)
        return data.SignedTx(
            txid=utils.add_0x_prefix(utils.keccak(encoded_tx).hex()),
            raw_tx=utils.add_0x_prefix(encoded_tx.hex()),
        )

    def get_token_info_by_address(self, token_address: str) -> Tuple[str, str, int]:
        return self.geth.get_token_info_by_address(token_address)

    def _build_unsigned_tx_dict(self, unsigned_tx: data.UnsignedTx) -> dict:
        output = unsigned_tx.outputs[0]
        is_erc20_transfer = bool(output.token_address)
        to_address = output.token_address if is_erc20_transfer else output.address
        value = 0 if is_erc20_transfer else output.value
        return {
            "to": utils.to_checksum_address(to_address),
            "value": value,
            "gas": unsigned_tx.fee_limit,
            "gasPrice": unsigned_tx.fee_price_per_unit,
            "nonce": unsigned_tx.nonce,
            "data": utils.add_0x_prefix(unsigned_tx.payload.get("data") or "0x"),
            "chainId": int(self.chain_info.chain_id),
        }
