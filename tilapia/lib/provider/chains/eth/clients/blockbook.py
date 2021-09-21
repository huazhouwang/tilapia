import datetime
import json
import math
import time
from decimal import Decimal
from typing import List, Optional

from tilapia.lib.basic.functional.require import require
from tilapia.lib.basic.functional.text import force_text
from tilapia.lib.basic.request.exceptions import RequestException, ResponseException
from tilapia.lib.basic.request.restful import RestfulRequest
from tilapia.lib.provider import data, exceptions, interfaces
from tilapia.lib.provider.chains.eth.clients import helper


def _normalize_iso_format(time_str: str) -> str:
    result = time_str.split(".")[0]  # exclude 9 digits microseconds
    if "Z" in time_str:
        result += "+00:00"
    elif "+" in time_str:
        result += "+" + time_str.split("+")[1]

    return result


class BlockBook(interfaces.ClientInterface, interfaces.SearchTransactionMixin):
    __raw_tx_status_mapping__ = {
        -1: data.TransactionStatus.PENDING,
        0: data.TransactionStatus.CONFIRM_REVERTED,
        1: data.TransactionStatus.CONFIRM_SUCCESS,
    }

    def __init__(self, url: str):
        self.restful = RestfulRequest(url, timeout=10)

    def get_info(self) -> data.ClientInfo:
        resp = self.restful.get("/api/v2")

        normalize_last_block_time = _normalize_iso_format(resp["blockbook"]["lastBlockTime"])

        try:
            last_block_time = datetime.datetime.fromisoformat(normalize_last_block_time).timestamp()
            is_ready = time.time() - last_block_time < 120
        except ValueError:
            is_ready = False

        return data.ClientInfo(
            name="blockbook",
            best_block_number=int(resp["blockbook"].get("bestHeight", 0)),
            is_ready=is_ready,
            desc=resp["blockbook"].get("about"),
        )

    def get_address(self, address: str) -> data.Address:
        resp = self._get_raw_address_info(address, details="basic")

        return data.Address(
            address=address,
            balance=int(resp["balance"]),
            nonce=int(resp["nonce"]),
            existing=bool(resp["txs"]),
        )

    def _get_raw_address_info(self, address: str, details: str, **kwargs) -> dict:
        resp = self.restful.get(f"/api/v2/address/{address}", params=dict(details=details, **kwargs))
        require(resp["address"].lower() == address.lower())
        return resp

    def get_balance(self, address: str, token_address: Optional[str] = None) -> int:
        if token_address is None:
            return super(BlockBook, self).get_balance(address)
        else:
            resp = self._get_raw_address_info(address, details="tokenBalances")
            tokens = {
                token_dict["contract"].lower(): token_dict["balance"]
                for token_dict in (resp.get("tokens") or ())
                if token_dict.get("contract") and token_dict.get("balance")
            }
            balance = tokens.get(token_address.lower(), 0)
            return int(balance)

    def get_transaction_by_txid(self, txid: str) -> data.Transaction:
        try:
            resp = self.restful.get(f"/api/v2/tx/{txid}")
            return self._populate_transaction(resp)
        except ResponseException as e:
            if e.response is not None and "not found" in force_text(e.response.text):
                raise exceptions.TransactionNotFound(txid)
            else:
                raise e

    def _populate_transaction(self, raw_tx: dict) -> data.Transaction:
        ethereum_data = raw_tx.get("ethereumSpecific") or {}
        token_transfers = raw_tx.get("tokenTransfers") or []

        block_header = (
            data.BlockHeader(
                block_hash=raw_tx["blockHash"],
                block_number=raw_tx["blockHeight"],
                block_time=raw_tx["blockTime"],
                confirmations=raw_tx["confirmations"],
            )
            if raw_tx.get("blockHash")
            else None
        )

        gas_limit = ethereum_data.get("gasLimit", 0)
        fee = data.TransactionFee(
            limit=int(gas_limit),
            used=int(ethereum_data.get("gasUsed") or gas_limit),
            price_per_unit=int(ethereum_data.get("gasPrice", 1)),
        )
        sender = (
            raw_tx["vin"][0]["addresses"][0].lower()
            if raw_tx.get("vin") and raw_tx["vin"][0].get("isAddress") and raw_tx["vin"][0].get("addresses")
            else ""
        )
        receiver = (
            raw_tx["vout"][0]["addresses"][0].lower()
            if raw_tx.get("vout") and raw_tx["vout"][0].get("isAddress") and raw_tx["vout"][0].get("addresses")
            else ""
        )
        value = int(raw_tx["vout"][0]["value"])

        return data.Transaction(
            txid=raw_tx["txid"],
            inputs=[
                data.TransactionInput(address=sender, value=value),
                *(
                    data.TransactionInput(
                        address=i.get("from", "").lower(),
                        value=int(i.get("value") or 0),
                        token_address=i["token"].lower(),
                    )
                    for i in token_transfers
                    if i.get("token")
                ),
            ],
            outputs=[
                data.TransactionOutput(address=receiver, value=value),
                *(
                    data.TransactionOutput(
                        address=i.get("to", "").lower(),
                        value=int(i.get("value") or 0),
                        token_address=i["token"].lower(),
                    )
                    for i in token_transfers
                    if i.get("token")
                ),
            ],
            status=self.__raw_tx_status_mapping__.get(ethereum_data.get("status")) or data.TransactionStatus.UNKNOWN,
            block_header=block_header,
            fee=fee,
            raw_tx=json.dumps(raw_tx),
            nonce=int(ethereum_data["nonce"]),
        )

    def search_txs_by_address(
        self,
        address: str,
        paginate: Optional[data.TxPaginate] = None,
    ) -> List[data.Transaction]:
        resp = self._get_raw_address_info(address, details="txs", **self._paging(paginate))
        txs = [self._populate_transaction(i) for i in resp.get("transactions", ())]

        return txs

    def search_txids_by_address(self, address: str, paginate: Optional[data.TxPaginate] = None) -> List[str]:
        resp = self._get_raw_address_info(address, details="txids", **self._paging(paginate))
        txids = [i for i in resp.get("txids", ())]

        return txids

    @staticmethod
    def _paging(paginate: Optional[data.TxPaginate]) -> dict:
        payload = {}
        if paginate is None:
            return payload

        if paginate.start_block_number is not None:
            payload["from"] = paginate.start_block_number

        if paginate.end_block_number is not None:
            payload["to"] = paginate.end_block_number

        if paginate.page_number is not None:
            payload["page"] = paginate.page_number

        if paginate.items_per_page is not None:
            payload["pageSize"] = paginate.items_per_page

        return payload

    def broadcast_transaction(self, raw_tx: str) -> data.TxBroadcastReceipt:
        if not raw_tx.startswith("0x"):
            raw_tx += "0x"

        try:
            resp = self.restful.get(f"/api/v2/sendtx/{raw_tx}")
        except ResponseException as e:
            try:
                resp = e.response.json()
            except ValueError:
                resp = dict()

        txid = resp.get("result")
        if txid:
            return data.TxBroadcastReceipt(is_success=True, receipt_code=data.TxBroadcastReceiptCode.SUCCESS, txid=txid)
        else:
            helper.raise_broadcast_error(resp.get("error") or "")

    def get_prices_per_unit_of_fee(self) -> data.PricesPerUnit:
        num_of_block = 10  # just a number, trezor does case what it is
        try:
            resp = self.restful.get(f"/api/v2/estimatefee/{num_of_block}")
        except RequestException:
            raise exceptions.FailedToGetGasPrices()

        slow = int(max(Decimal(resp["result"]) * 10 ** 18, 1))  # Blockbook returns price in Ether
        normal = math.ceil(slow * 1.25)
        fast = math.ceil(normal * 1.2)  # 1.25 * 1.2 = 1.5

        return data.PricesPerUnit(
            normal=data.EstimatedTimeOnPrice(price=normal, time=180),
            others=[
                data.EstimatedTimeOnPrice(price=slow, time=600),
                data.EstimatedTimeOnPrice(price=fast, time=60),
            ],
        )
