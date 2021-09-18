import decimal
import json
from typing import List, Optional

from common.basic.request.exceptions import RequestException
from common.basic.request.restful import RestfulRequest
from common.provider.chains.eth.clients import helper
from common.provider.data import (
    Address,
    BlockHeader,
    ClientInfo,
    EstimatedTimeOnPrice,
    PricesPerUnit,
    Transaction,
    TransactionFee,
    TransactionInput,
    TransactionOutput,
    TransactionStatus,
    TxBroadcastReceipt,
    TxBroadcastReceiptCode,
    TxPaginate,
)
from common.provider.exceptions import FailedToGetGasPrices
from common.provider.interfaces import ClientInterface, SearchTransactionMixin


class Etherscan(ClientInterface, SearchTransactionMixin):
    def __init__(self, url: str, api_keys: List[str] = None):
        self.restful = RestfulRequest(url, timeout=10)
        self.api_key = api_keys[0] if api_keys else None

    def _call_action(self, module: str, action: str, **kwargs) -> dict:
        kwargs = kwargs if kwargs is not None else dict()
        kwargs.update(dict(module=module, action=action))
        return self._call_with_api_key("/api", data=kwargs)

    def _call_with_api_key(self, path: str, data: dict) -> dict:
        if self.api_key:
            data["apikey"] = self.api_key

        resp = self.restful.post(path, data=data)
        return resp

    def get_info(self) -> ClientInfo:
        resp = self._call_action("proxy", "eth_blockNumber")
        return ClientInfo(
            name="etherscan",
            best_block_number=int(resp["result"], base=16),
            is_ready=True,
        )

    def get_address(self, address: str) -> Address:
        resp = self._call_action("account", "balance", address=address, tag="latest")
        balance = int(resp["result"])

        resp = self._call_action("proxy", "eth_getTransactionCount", address=address)
        nonce = int(resp["result"], base=16)
        return Address(address=address, balance=balance, nonce=nonce, existing=(bool(balance) or bool(nonce)))

    def get_balance(self, address: str, token_address: Optional[str] = None) -> int:
        if token_address is None:
            return super(Etherscan, self).get_balance(address)
        else:
            resp = self._call_action("account", "tokenbalance", address=address, contractaddress=token_address)
            return int(resp.get("result", 0))

    def get_transaction_by_txid(self, txid: str) -> Transaction:
        resp = self._call_action("proxy", "eth_getTransactionByHash", txhash=txid)
        raw_tx = resp["result"]

        if raw_tx.get("blockHash"):
            block_info = self._call_action("proxy", "eth_getBlockByNumber", tag=raw_tx["blockNumber"], boolean=False)[
                "result"
            ]
            block_header = BlockHeader(
                block_hash=block_info["hash"],
                block_number=int(block_info["number"], base=16),
                block_time=int(block_info["timestamp"], base=16),
            )
        else:
            block_header = None

        if block_header:
            resp = self._call_action("proxy", "eth_getTransactionReceipt", txhash=txid)
            receipt = resp["result"]
        else:
            receipt = None

        status = TransactionStatus.PENDING
        receipt_status = receipt["status"] if receipt else None
        if receipt_status == "0x0":
            status = TransactionStatus.CONFIRM_REVERTED
        elif receipt_status == "0x1":
            status = TransactionStatus.CONFIRM_SUCCESS

        gas_limit = int(raw_tx["gas"], base=16)
        gas_used = int(receipt["gasUsed"], base=16) if receipt else None
        gas_used = gas_used or gas_limit
        fee = TransactionFee(
            limit=gas_limit,
            used=gas_used,
            price_per_unit=int(raw_tx["gasPrice"], base=16),
        )
        sender = raw_tx.get("from", "").lower()
        receiver = raw_tx.get("to", "").lower()
        value = int(raw_tx.get("value", "0x0"), base=16)

        return Transaction(
            txid=raw_tx["hash"],
            block_header=block_header,
            inputs=[TransactionInput(address=sender, value=value)],
            outputs=[TransactionOutput(address=receiver, value=value)],
            status=status,
            fee=fee,
            raw_tx=json.dumps(raw_tx),
            nonce=int(raw_tx["nonce"], base=16),
        )

    @staticmethod
    def _paging(paginate: Optional[TxPaginate]) -> dict:
        payload = {}
        if paginate is None:
            return payload

        if paginate.start_block_number is not None:
            payload["startblock"] = paginate.start_block_number

        if paginate.end_block_number is not None:
            payload["endblock"] = paginate.end_block_number

        if paginate.page_number is not None:
            payload["page"] = paginate.page_number

        if paginate.items_per_page is not None:
            payload["offset"] = paginate.items_per_page

        return payload

    def search_txs_by_address(self, address: str, paginate: Optional[TxPaginate] = None) -> List[Transaction]:
        resp = self._call_action("account", "txlist", address=address, sort="desc", **self._paging(paginate))
        raw_txs = resp["result"]

        txs = []
        if not isinstance(raw_txs, list):
            return txs

        for raw_tx in raw_txs:
            block_header = BlockHeader(
                block_hash=raw_tx["blockHash"],
                block_number=int(raw_tx["blockNumber"]),
                block_time=int(raw_tx["timeStamp"]),
            )

            status = TransactionStatus.PENDING
            receipt_status = raw_tx.get("txreceipt_status")
            if receipt_status == "0":
                status = TransactionStatus.CONFIRM_REVERTED
            elif receipt_status == "1":
                status = TransactionStatus.CONFIRM_SUCCESS

            gas_limit = int(raw_tx["gas"])
            gas_used = int(raw_tx.get("gasUsed")) or gas_limit
            fee = TransactionFee(limit=gas_limit, used=gas_used, price_per_unit=int(raw_tx["gasPrice"]))
            sender = raw_tx.get("from", "").lower()
            receiver = raw_tx.get("to", "").lower()
            value = int(raw_tx.get("value", "0"))

            tx = Transaction(
                txid=raw_tx["hash"],
                block_header=block_header,
                inputs=[TransactionInput(address=sender, value=value)],
                outputs=[TransactionOutput(address=receiver, value=value)],
                status=status,
                fee=fee,
                raw_tx=json.dumps(raw_tx),
                nonce=int(raw_tx["nonce"]),
            )
            txs.append(tx)

        return txs

    def broadcast_transaction(self, raw_tx: str) -> TxBroadcastReceipt:
        if not raw_tx.startswith("0x"):
            raw_tx += "0x"

        resp = self._call_action("proxy", "eth_sendRawTransaction", hex=raw_tx)

        txid = resp.get("result")
        if txid:
            return TxBroadcastReceipt(is_success=True, receipt_code=TxBroadcastReceiptCode.SUCCESS, txid=txid)
        else:
            helper.raise_broadcast_error(resp.get("error", {}).get("message") or "")

    def get_prices_per_unit_of_fee(self) -> PricesPerUnit:
        try:
            resp = self._call_action("gastracker", "gasoracle")
        except RequestException:
            raise FailedToGetGasPrices()

        result = resp.get("result")
        if result is None:
            raise FailedToGetGasPrices()

        # Etherscan returns price in Gwei
        slow = int(max(decimal.Decimal(result["SafeGasPrice"]) * 10 ** 9, 1))
        normal = int(max(decimal.Decimal(result["ProposeGasPrice"]) * 10 ** 9, 1))
        fast = int(max(decimal.Decimal(result["FastGasPrice"]) * 10 ** 9, 1))

        return PricesPerUnit(
            normal=EstimatedTimeOnPrice(price=normal, time=180),
            others=[
                EstimatedTimeOnPrice(price=slow, time=600),
                EstimatedTimeOnPrice(price=fast, time=60),
            ],
        )
