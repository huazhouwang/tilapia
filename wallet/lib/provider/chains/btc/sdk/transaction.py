import logging
import math
from typing import Any, Iterable, List, Tuple

from pycoin.cmds import dump as pycoin_dump
from pycoin.coins import tx_utils as pycoin_tx_utils
from pycoin.coins.bitcoin import Tx as pycoin_tx
from pycoin.encoding import bytes32 as pycoin_bytes32
from pycoin.encoding import sec as pycoin_sec

from wallet.lib.basic.functional.require import require
from wallet.lib.provider import data
from wallet.lib.secret import interfaces as secret_interfaces

logger = logging.getLogger("app.chain")

# See https://bitcoinops.org/en/tools/calc-size/
HEADER_VSIZE = 10  # nVersion(4) + InputCount(1) + OutputCount(1) + nLockTime(4)
SEGWIT_HEADER_EXTENSION_VSIZE = 0.5  # SegwitMarker(0.25) + SegwitFlag(0.25)
INPUT_VSIZE_LOOKUP = {
    "P2PKH": 148,  # OutPoint(36) + ScriptSigLength(1) + ScriptSig(107) + nSequence(4)
    "P2WPKH": 68,  # OutPoint(36) + ScriptSigLength(1) + nSequence(4) + WitnessItem(27)
    "P2WPKH-P2SH": 91,  # OutPoint(36) + ScriptSigLength(1) + ScriptSig(23) + nSequence(4) + WitnessItem(27)
}
SEGWIT_INPUT_WITNESS_ITEM_COUNT_VSIZE = 0.25
OUTPUT_VSIZE_LOOKUP = {
    "P2PKH": 34,  # nValue(8) + ScriptPubKeyLength(1) + ScriptPubKey(25)
    "P2WPKH": 31,  # nValue(8) + ScriptPubKeyLength(1) + ScriptPubKey(22)
    "P2WPKH-P2SH": 32,  # nValue(8) + ScriptPubKeyLength(1) + ScriptPubKey(23)
}
OP_RETURN_OUTPUT_PREFIX_VSIZE = (
    12  # nValue(8) + ScriptPubKeyLength(1) + OP_RETURN(1) + OP_PUSHDATA1(1) ReturnDataLength(1)
)

PLACEHOLDER_VSIZE = 79  # calculate_vsize(["P2WPKH"], [])
TX_VERSION = 1
TX_OP_RETURN_SIZE_LIMIT = 80


def op_return_as_buffer(op_return: str) -> bytes:
    if op_return.startswith("0x"):
        return bytes.fromhex(op_return)
    else:
        return op_return.encode()


def calculate_vsize(
    input_encodings: List[str],
    output_encodings: List[str],
    op_return: str = None,
    op_return_size_limit: int = 80,
) -> int:
    vsize = HEADER_VSIZE
    is_segwit = any("P2WPKH" in i for i in input_encodings)
    if is_segwit:
        vsize += SEGWIT_HEADER_EXTENSION_VSIZE

    vsize += sum(INPUT_VSIZE_LOOKUP[i] for i in input_encodings)
    if is_segwit:
        vsize += SEGWIT_INPUT_WITNESS_ITEM_COUNT_VSIZE

    vsize += sum(OUTPUT_VSIZE_LOOKUP[i] for i in output_encodings)

    if op_return:
        size_of_op_return = len(op_return_as_buffer(op_return))
        vsize += OP_RETURN_OUTPUT_PREFIX_VSIZE * math.ceil(size_of_op_return / op_return_size_limit)
        vsize += size_of_op_return

    return math.ceil(vsize)


def create_spendables_from_inputs(network: Any, inputs: List[data.TransactionInput]) -> List[pycoin_tx.Spendable]:
    return [
        network.tx.Spendable.from_dict(
            {
                "coin_value": i.value,
                "script_hex": network.contract.for_address(i.address).hex(),
                "tx_hash_hex": i.utxo.txid,
                "tx_out_index": i.utxo.vout,
            }
        )
        for i in inputs
    ]


def create_pycoin_tx(
    network: Any, unsigned_tx: data.UnsignedTx, version: int, op_return_size_limit: int
) -> pycoin_tx.Tx:
    tx_inputs = unsigned_tx.inputs
    tx_outputs = unsigned_tx.outputs
    require(tx_inputs and tx_outputs)

    spendables = create_spendables_from_inputs(network, unsigned_tx.inputs)
    payables = [(i.address, i.value) for i in tx_outputs]

    input_count = sum(i.value for i in tx_inputs)
    output_count = sum(i.value for i in tx_outputs)

    actual_fee = input_count - output_count
    require(actual_fee > 0, f"Invalid fee: {actual_fee}")
    declare_fee = unsigned_tx.fee_limit * unsigned_tx.fee_price_per_unit
    fee_deviation = declare_fee - actual_fee
    if abs(fee_deviation) >= 10:
        logger.warning(
            f"Excessive fee deviation. declare_fee: {declare_fee}, actual_fee: {actual_fee}, deviation: {fee_deviation}"
        )

    tx = pycoin_tx_utils.create_tx(network, spendables, payables, fee=actual_fee, version=version)

    if unsigned_tx.payload and unsigned_tx.payload.get("op_return"):
        op_return: bytes = unsigned_tx.payload["op_return"].encode()

        try:
            scripts = []
            for i in range(0, len(op_return), op_return_size_limit):
                cur_op_return = op_return[i : i + op_return_size_limit]
                script = network.script.compile(f"OP_RETURN [{cur_op_return.hex()}]")
                scripts.append(script)
        except Exception as e:
            logger.exception(f"Error in compiling OP_RETURN script. op_return: {op_return.hex()}, error: {e}")
            scripts = []

        tx.txs_out.extend((network.tx.TxOut(0, i) for i in scripts))

    return tx


class _WrappedSigner(object):
    def __init__(self, signer: secret_interfaces.SignerInterface, generator: any):
        self.signer = signer
        self.generator = generator

    def order(self) -> int:
        return self.generator.order()

    def sign(self, secret_exponent: int, digest_int: int) -> Tuple[int, int]:
        if digest_int == 0:
            raise ValueError()

        digest = pycoin_bytes32.to_bytes_32(digest_int)
        sig, _ = self.signer.sign(digest)
        r, s = pycoin_bytes32.from_bytes_32(sig[:32]), pycoin_bytes32.from_bytes_32(sig[32:])
        return r, s


def build_hash160_lookup(network: any, signers: Iterable[secret_interfaces.SignerInterface]) -> dict:
    """
    See pycoin.solve.utils.build_hash160_lookup
    """
    lookup = {}

    for i in signers:
        wrapped = _WrappedSigner(i, network.generator)
        pubkey = i.get_pubkey(compressed=True)
        pubkey_hash = network.keys.public(pubkey).hash160(is_compressed=True)
        public_pair = pycoin_sec.sec_to_public_pair(pubkey, generator=wrapped.generator)
        lookup[pubkey_hash] = (
            None,
            public_pair,
            True,
            wrapped,
        )

    return lookup


def build_p2sh_lookup(network: any, signers: Iterable[secret_interfaces.SignerInterface]) -> dict:
    scripts = []

    for i in signers:
        pubkey = i.get_pubkey(compressed=True)
        pubkey_hash = network.keys.public(pubkey).hash160(is_compressed=True)
        scripts.append(network.script.compile(f"OP_0 {pubkey_hash.hex()}"))

    return network.tx.solve.build_p2sh_lookup(scripts)


def debug_dump_tx(network: any, tx: pycoin_tx.Tx) -> str:
    output = []
    pycoin_dump.dump_tx(
        output, tx, network, verbose_signature=False, disassembly_level=False, do_trace=False, use_pdb=False
    )
    return "\n".join(output)
