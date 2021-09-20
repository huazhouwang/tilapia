import abc
import base64
import logging
from typing import Any, Dict, Iterable, List

from pycoin.coins.bitcoin import Tx as pycoin_tx
from trezorlib import btc as trezor_btc
from trezorlib import messages as trezor_messages

from wallet.lib.basic import bip44
from wallet.lib.coin import data as coin_data
from wallet.lib.hardware import interfaces as hardware_interfaces
from wallet.lib.provider import data, interfaces
from wallet.lib.provider.chains.btc.clients import blockbook
from wallet.lib.provider.chains.btc.sdk import transaction

logger = logging.getLogger("app.chain")


class BTCHardwareMixin(interfaces.HardwareSupportingMixin, abc.ABC):
    chain_info: coin_data.ChainInfo

    @property
    @abc.abstractmethod
    def network(self) -> Any:
        pass

    @property
    @abc.abstractmethod
    def tx_version(self) -> int:
        pass

    @property
    @abc.abstractmethod
    def tx_op_return_size_limit(self) -> int:
        pass

    @property
    @abc.abstractmethod
    def client(self) -> blockbook.BlockBook:
        pass

    def hardware_get_xpub(
        self,
        hardware_client: hardware_interfaces.HardwareClientInterface,
        bip44_path: bip44.BIP44Path,
        confirm_on_device: bool = False,
    ) -> str:
        script_type = _get_hardware_input_secret_type_from_bip44_path(bip44_path)

        return trezor_btc.get_public_node(
            hardware_client,
            n=bip44_path.to_bip44_int_path(),
            show_display=1 if confirm_on_device else 0,
            coin_name=self.chain_info.name,
            script_type=script_type,
        ).xpub

    def hardware_get_address(
        self,
        hardware_client: hardware_interfaces.HardwareClientInterface,
        bip44_path: bip44.BIP44Path,
        confirm_on_device: bool = False,
    ) -> str:
        script_type = _get_hardware_input_secret_type_from_bip44_path(bip44_path)

        address = trezor_btc.get_address(
            hardware_client,
            coin_name=self.chain_info.name,
            n=bip44_path.to_bip44_int_path(),
            show_display=confirm_on_device,
            script_type=script_type,
        )
        return address

    def _collect_raw_txs(self, txids: Iterable[str]) -> Dict[str, str]:
        raw_txs = {}

        for txid in txids:
            tx = self.client.get_transaction_by_txid(txid)
            raw_txs[txid] = tx.raw_tx

        return raw_txs

    def hardware_sign_transaction(
        self,
        hardware_client: hardware_interfaces.HardwareClientInterface,
        unsigned_tx: data.UnsignedTx,
        bip44_path_of_signers: Dict[str, bip44.BIP44Path],
    ) -> data.SignedTx:
        prev_txids = set(i.utxo.txid for i in unsigned_tx.inputs)
        prev_raw_txs = self._collect_raw_txs(prev_txids)
        prev_txs = {bytes.fromhex(txid): _build_prev_tx(self.network, raw_tx) for txid, raw_tx in prev_raw_txs.items()}

        inputs = _build_hardware_inputs(unsigned_tx.inputs, bip44_path_of_signers)
        outputs = _build_hardware_outputs(unsigned_tx.outputs, unsigned_tx.payload, self.tx_op_return_size_limit)

        # noinspection PyTypeChecker
        _, raw_tx_bytes = trezor_btc.sign_tx(
            hardware_client, self.chain_info.name, inputs, outputs, prev_txes=prev_txs, version=self.tx_version
        )

        tx: pycoin_tx.Tx = self.network.tx.from_bin(raw_tx_bytes)
        spendables = transaction.create_spendables_from_inputs(self.network, unsigned_tx.inputs)
        tx.set_unspents(spendables)
        self._check_tx_after_signed(tx)

        return data.SignedTx(txid=tx.id(), raw_tx=tx.as_hex())

    @abc.abstractmethod
    def _check_tx_after_signed(self, tx: pycoin_tx.Tx):
        pass

    def hardware_sign_message(
        self,
        hardware_client: hardware_interfaces.HardwareClientInterface,
        message: str,
        signer_bip44_path: bip44.BIP44Path,
    ) -> str:
        script_type = _get_hardware_input_secret_type_from_bip44_path(signer_bip44_path)

        signature_bytes = trezor_btc.sign_message(
            hardware_client,
            coin_name=self.chain_info.name,
            n=signer_bip44_path.to_bip44_int_path(),
            message=message,
            script_type=script_type,
        ).signature
        return base64.b64encode(signature_bytes).decode()

    def hardware_verify_message(
        self,
        hardware_client: hardware_interfaces.HardwareClientInterface,
        address: str,
        message: str,
        signature: str,
    ) -> bool:
        signature_bytes = base64.b64decode(signature)
        return trezor_btc.verify_message(
            hardware_client,
            coin_name=self.chain_info.name,
            address=address,
            signature=signature_bytes,
            message=message,
        )


def _build_hardware_inputs(
    inputs: List[data.TransactionInput], bip44_path_of_signers: Dict[str, bip44.BIP44Path]
) -> List[trezor_messages.TxInputType]:
    hardware_inputs = []

    for i in inputs:
        bip44_path = bip44_path_of_signers[i.address]
        script_type = _get_hardware_input_secret_type_from_bip44_path(bip44_path)
        hardware_input = dict(
            script_type=script_type,
            address_n=bip44_path.to_bip44_int_path(),
            prev_hash=bytes.fromhex(i.utxo.txid),
            prev_index=int(i.utxo.vout),
            amount=int(i.utxo.value),
        )
        hardware_inputs.append(trezor_messages.TxInputType(**hardware_input))

    return hardware_inputs


def _build_hardware_outputs(
    outputs: List[data.TransactionOutput], payload: dict, op_return_size_limit: int
) -> List[trezor_messages.TxOutputType]:
    hardware_outputs = []

    for i in outputs:
        hardware_output = dict(amount=int(i.value))
        is_change = i.payload.get("is_change", False)
        bip44_path_str = i.payload.get("bip44_path", None)

        if is_change and bip44_path_str:
            bip44_path = bip44.BIP44Path.from_bip44_path(bip44_path_str)
            script_type = _get_hardware_output_secret_type_from_bip44_path(bip44_path)
            hardware_output.update(
                dict(
                    script_type=script_type,
                    address_n=bip44_path.to_bip44_int_path(),
                )
            )
        else:
            hardware_output.update(dict(script_type=trezor_messages.OutputScriptType.PAYTOADDRESS, address=i.address))

        hardware_outputs.append(trezor_messages.TxOutputType(**hardware_output))

    if payload and payload.get("op_return"):
        op_return: bytes = payload["op_return"].encode()
        if len(op_return) > op_return_size_limit:
            logger.warning(
                f"OP_RETURN exceed limit for hardware. "
                f"op_return_size_limit: {op_return_size_limit}, now got: {len(op_return)}"
            )
            op_return = op_return[:op_return_size_limit]

        hardware_outputs.append(
            trezor_messages.TxOutputType(
                amount=0, script_type=trezor_messages.OutputScriptType.PAYTOOPRETURN, op_return_data=op_return
            )
        )

    return hardware_outputs


def _build_prev_tx(network, raw_tx: str) -> trezor_messages.TransactionType:
    tx: pycoin_tx.Tx = network.tx.from_hex(raw_tx)

    hardware_tx = trezor_messages.TransactionType()
    hardware_tx.version = int(tx.version)
    hardware_tx.lock_time = int(tx.lock_time)
    hardware_tx.inputs = [
        trezor_messages.TxInputType(
            prev_hash=tx_in.previous_hash[::-1],
            prev_index=tx_in.previous_index,
            script_sig=tx_in.script,
            sequence=tx_in.sequence,
        )
        for tx_in in tx.txs_in
    ]
    hardware_tx.bin_outputs = [
        trezor_messages.TxOutputBinType(amount=tx_out.coin_value, script_pubkey=tx_out.script) for tx_out in tx.txs_out
    ]
    return hardware_tx


def _get_hardware_input_secret_type_from_bip44_path(bip44_path: bip44.BIP44Path) -> int:
    purpose = bip44_path.index_of(bip44.BIP44Level.PURPOSE)

    if purpose in (84, 48):
        script_type = trezor_messages.InputScriptType.SPENDWITNESS
    elif purpose == 49:
        script_type = trezor_messages.InputScriptType.SPENDP2SHWITNESS
    elif purpose == 44:
        script_type = trezor_messages.InputScriptType.SPENDADDRESS
    else:
        raise Exception(f"Invalid purpose: {purpose}")

    return script_type


def _get_hardware_output_secret_type_from_bip44_path(bip44_path: bip44.BIP44Path) -> int:
    purpose = bip44_path.index_of(bip44.BIP44Level.PURPOSE)

    if purpose in (84, 48):
        script_type = trezor_messages.OutputScriptType.PAYTOWITNESS
    elif purpose == 49:
        script_type = trezor_messages.OutputScriptType.PAYTOP2SHWITNESS
    elif purpose == 44:
        script_type = trezor_messages.OutputScriptType.PAYTOADDRESS
    else:
        raise Exception(f"Invalid purpose: {purpose}")

    return script_type
