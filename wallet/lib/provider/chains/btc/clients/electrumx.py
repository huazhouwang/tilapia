import hashlib
import socket
from decimal import Decimal
from typing import List, Set
from urllib import parse as urllib_parse

import peewee
import requests

from wallet.lib.basic.request import exceptions as request_exceptions
from wallet.lib.basic.request import json_rpc
from wallet.lib.provider import data, exceptions, interfaces
from wallet.lib.provider.chains.btc.clients.blockbook import BTC_PER_KBYTES__TO__SAT_PER_BYTE, MIN_SAT_PER_BYTE
from wallet.lib.provider.chains.btc.sdk import network

BTC__TO__SAT = pow(10, 8)


class _Adapter(object):
    END_POINT = b"\x0a"

    def send(self, request: requests.PreparedRequest, timeout: int = None, **kwargs) -> requests.Response:
        url_parsed = urllib_parse.urlsplit(request.url)

        with socket.create_connection((url_parsed.hostname, url_parsed.port or 500001), timeout or 10) as s:
            s.sendall(request.body + self.END_POINT)
            content = self.recvall(s)

            response = requests.Response()
            response.status_code = 200
            response.encoding = "utf-8"
            response._content = content
            return response

    @classmethod
    def recvall(cls, s: socket.socket):
        buffer_size = 4096
        buffer = bytearray()

        while True:
            part = s.recv(buffer_size)
            buffer.extend(part)

            if len(part) < buffer_size and buffer.endswith(cls.END_POINT):
                break

        if buffer.endswith(cls.END_POINT):
            buffer.pop()

        return bytes(buffer)


def _populate_transaction(tx: dict, prev_txs_lookup: dict) -> data.Transaction:
    inputs = []

    for i in tx.get("vin", ()):
        prev_txid = i.get("txid")
        vout = int(i.get("vout", -1))
        prev_tx = prev_txs_lookup.get(prev_txid)

        if not prev_tx or vout < 0:
            continue

        address = prev_tx["vout"][vout]["scriptPubKey"].get("address", "")
        value = int(Decimal(str(prev_tx["vout"][vout].get("value", 0))) * BTC__TO__SAT)
        inputs.append(
            data.TransactionInput(
                address=address, value=value, utxo=data.UTXO(txid=prev_txid, vout=int(i.get("vout", -1)), value=value)
            )
        )

    outputs = [
        data.TransactionOutput(address=i["scriptPubKey"]["address"], value=int(Decimal(str(i["value"])) * BTC__TO__SAT))
        for i in tx.get("vout", ())
        if i.get("scriptPubKey", {}).get("address")
    ]

    block_header = (
        data.BlockHeader(
            block_hash=tx["blockhash"],
            block_number=0,  # todo
            block_time=tx["blocktime"],
            confirmations=tx["confirmations"],
        )
        if tx.get("blockhash")
        else None
    )

    total_input = sum(i.value for i in inputs)
    total_output = sum(i.value for i in outputs)
    total_fee = max(0, total_input - total_output)
    fee_limit = tx.get("vsize", 0)
    price_per_unit = int(total_fee / fee_limit) if fee_limit else 0
    fee = data.TransactionFee(limit=fee_limit, used=fee_limit, price_per_unit=price_per_unit)

    return data.Transaction(
        txid=tx.get("txid") or "",
        inputs=inputs,
        outputs=outputs,
        status=data.TransactionStatus.CONFIRM_SUCCESS if block_header is not None else data.TransactionStatus.PENDING,
        fee=fee,
        block_header=block_header,
        raw_tx=tx.get("hex") or "",
    )


class ElectrumX(
    interfaces.ClientChainBinding,
    interfaces.ClientInterface,
    interfaces.BatchGetAddressMixin,
    interfaces.SearchUTXOMixin,
):
    def __init__(self, url: str):
        super().__init__()
        self.rpc = json_rpc.JsonRPCRequest(
            url, session_initializer=lambda session: session.adapters.setdefault("tcp://", _Adapter())
        )
        self._network = None

    @property
    def network(self):
        if self._network is None:
            self._network = network.get_network_by_chain_code(self.chain_info.chain_code)

        return self._network

    def get_info(self) -> data.ClientInfo:
        resp = self.rpc.call("blockchain.headers.subscribe", [])
        best_block_number = resp.get("height") or 0
        return data.ClientInfo(
            name="ElectrumX",
            best_block_number=best_block_number,
            is_ready=best_block_number > 0,
        )

    def get_address(self, address: str) -> data.Address:
        return self.batch_get_address([address])[0]

    def batch_get_address(self, addresses: List[str]) -> List[data.Address]:
        script_hashes = [self._electrum_script_hash_of_address(i) for i in addresses]
        calls = []

        for script_hash in script_hashes:
            calls.append(("blockchain.scripthash.get_balance", [script_hash]))
            calls.append(("blockchain.scripthash.get_history", [script_hash]))

        result = []
        resp = self.rpc.batch_call(calls)

        for i, address in enumerate(addresses):
            balance_resp, history_resp = resp[i * 2], resp[i * 2 + 1]
            confirmed, unconfirmed = balance_resp.get("confirmed", 0), balance_resp.get("unconfirmed", 0)
            unconfirmed = min(unconfirmed, 0)  # Only use it when some outputs are pending
            balance = max(confirmed + unconfirmed, 0)

            existing = isinstance(history_resp, list) and len(history_resp) > 0

            result.append(
                data.Address(
                    address=address,
                    balance=balance,
                    existing=existing,
                )
            )

        return result

    def _electrum_script_hash_of_address(self, address: str) -> str:
        parsed_address = self.network.parse.address(address)
        script_hash = hashlib.sha256(parsed_address.script()).digest()
        script_hash = bytes(reversed(script_hash))
        return script_hash.hex()

    def get_prices_per_unit_of_fee(self) -> data.PricesPerUnit:
        fast, normal, slow = self.rpc.batch_call([("blockchain.estimatefee", [i]) for i in (1, 3, 5)])

        def _normalize(value):
            btc_per_kbytes = Decimal(str(value))
            sat_per_byte = btc_per_kbytes * BTC_PER_KBYTES__TO__SAT_PER_BYTE
            return int(max(sat_per_byte, MIN_SAT_PER_BYTE))

        blocktime_seconds = self.chain_info.blocktime_seconds or 600

        return data.PricesPerUnit(
            normal=data.EstimatedTimeOnPrice(price=_normalize(normal), time=blocktime_seconds * 3),
            others=[
                data.EstimatedTimeOnPrice(price=_normalize(fast), time=blocktime_seconds),
                data.EstimatedTimeOnPrice(price=_normalize(slow), time=blocktime_seconds * 5),
            ],
        )

    def search_utxos_by_address(self, address: str) -> List[data.UTXO]:
        script_hash = self._electrum_script_hash_of_address(address)
        resp = self.rpc.call("blockchain.scripthash.listunspent", [script_hash])
        result = []

        if isinstance(resp, list):
            resp = (i for i in resp if i.get("height", 0) > 0)  # todo coinbase?
            result.extend(data.UTXO(value=i["value"], txid=i["tx_hash"], vout=i["tx_pos"]) for i in resp)

        return result

    def broadcast_transaction(self, raw_tx: str) -> data.TxBroadcastReceipt:
        try:
            txid = self.rpc.call("blockchain.transaction.broadcast", [raw_tx])
        except request_exceptions.JsonRPCException as e:
            error = e.json_response.get("error") or {}
            error_message = error.get("message") or None
            if error_message or "Transaction already in block chain" in error_message:
                raise exceptions.TransactionAlreadyKnown(error) from e
            else:
                raise exceptions.UnknownBroadcastError(error) from e
        else:
            is_success = isinstance(txid, str) and len(txid) == 64
            return data.TxBroadcastReceipt(
                is_success=is_success,
                receipt_code=data.TxBroadcastReceiptCode.SUCCESS
                if is_success
                else data.TxBroadcastReceiptCode.UNEXPECTED_FAILED,
                txid=txid if is_success else "",
            )

    def get_transaction_by_txid(self, txid: str) -> data.Transaction:
        tx = self.rpc.call("blockchain.transaction.get", [txid, True])
        prev_txids = {i["txid"] for i in tx["vin"]}
        prev_txs_lookup = self._batch_get_transaction_by_txids(prev_txids)
        return _populate_transaction(tx, prev_txs_lookup)

    def _batch_get_transaction_by_txids(self, txids: Set[str]) -> dict:
        result = {}

        for batch in peewee.chunked(txids, 10):
            calls = [("blockchain.transaction.get", [i, True]) for i in batch]
            txs: List[dict] = self.rpc.batch_call(calls, ignore_errors=True)

            for tx in txs:
                if isinstance(tx, dict) and tx:
                    result[tx["txid"]] = tx

        return result
