import logging
from decimal import Decimal
from typing import List, Optional

from wallet.lib.basic.functional.text import force_text
from wallet.lib.basic.request import exceptions as request_exceptions
from wallet.lib.basic.request import restful
from wallet.lib.provider import data, exceptions, interfaces

logger = logging.getLogger("app.chain")

MIN_SAT_PER_BYTE = Decimal(1)
BTC_PER_KBYTES__TO__SAT_PER_BYTE = pow(10, 5)


def _populate_transaction(json_tx: dict) -> data.Transaction:
    inputs = [
        data.TransactionInput(
            address=i["addresses"][0],
            value=int(i.get("value") or 0),
            utxo=data.UTXO(
                txid=i.get("txid") or "",
                vout=int(i.get("vout", -1)),
                value=int(i.get("value") or 0),
            ),
        )
        for i in json_tx.get("vin", ())
        if i.get("isAddress", False) is True and i.get("addresses")
    ]
    outputs = [
        data.TransactionOutput(
            address=i["addresses"][0],
            value=int(i.get("value") or 0),
        )
        for i in json_tx.get("vout", ())
        if i.get("isAddress", False) is True and i.get("addresses")
    ]

    block_header = (
        data.BlockHeader(
            block_hash=json_tx["blockHash"],
            block_number=json_tx["blockHeight"],
            block_time=json_tx["blockTime"],
            confirmations=json_tx["confirmations"],
        )
        if json_tx.get("blockHash")
        else None
    )
    fee = data.TransactionFee(limit=int(json_tx.get("fees") or 0), used=int(json_tx.get("fees") or 0), price_per_unit=1)

    return data.Transaction(
        txid=json_tx.get("txid") or "",
        inputs=inputs,
        outputs=outputs,
        status=data.TransactionStatus.CONFIRM_SUCCESS if block_header is not None else data.TransactionStatus.PENDING,
        fee=fee,
        block_header=block_header,
        raw_tx=json_tx.get("hex") or "",
    )


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


class BlockBook(
    interfaces.ClientChainBinding,
    interfaces.ClientInterface,
    interfaces.SearchUTXOMixin,
    interfaces.SearchTransactionMixin,
):
    def __init__(self, url: str):
        self.restful = restful.RestfulRequest(url, timeout=10)

    def get_info(self) -> data.ClientInfo:
        resp = self.restful.get("/api/v2")
        backend = resp.get("backend") or {}

        return data.ClientInfo(
            name="blockbook",
            best_block_number=backend.get("blocks") or 0,
            is_ready=bool(backend),
        )

    def get_address(self, address: str) -> data.Address:
        resp = self.restful.get(f"/api/v2/address/{address}", params=dict(details="basic"))
        unconfirmed_balance = min(
            int(resp.get("unconfirmedBalance") or 0), 0
        )  # Only use it when some outputs are pending
        return data.Address(
            address=address,
            balance=max(0, int(resp.get("balance") or 0) + unconfirmed_balance),
            existing=int(resp.get("txs") or 0) > 0,
        )

    def get_transaction_by_txid(self, txid: str) -> data.Transaction:
        try:
            resp = self.restful.get(f"/api/v2/tx/{txid}")
            return _populate_transaction(resp)
        except request_exceptions.ResponseException as e:
            if e.response is not None and "not found" in force_text(e.response.text):
                raise exceptions.TransactionNotFound(txid)
            else:
                raise e

    def broadcast_transaction(self, raw_tx: str) -> data.TxBroadcastReceipt:
        try:
            resp = self.restful.get(f"/api/v2/sendtx/{raw_tx}")
        except request_exceptions.ResponseException as e:
            try:
                resp = e.response.json()
            except ValueError:
                resp = {}

            error = resp.get("error", "")
            if isinstance(error, str) and "Transaction already in block chain" in error:
                raise exceptions.TransactionAlreadyKnown(error) from e
            else:
                raise exceptions.UnknownBroadcastError(error) from e
        else:
            txid = resp.get("result")
            is_success = isinstance(txid, str) and len(txid) == 64
            return data.TxBroadcastReceipt(
                is_success=is_success,
                receipt_code=data.TxBroadcastReceiptCode.SUCCESS
                if is_success
                else data.TxBroadcastReceiptCode.UNEXPECTED_FAILED,
                txid=txid if is_success else "",
            )

    def get_normal_fee_rate(self) -> Decimal:
        resp = self.restful.get("/api/v2/estimatefee/3")
        return max(MIN_SAT_PER_BYTE, Decimal(resp.get("result") or 0) * BTC_PER_KBYTES__TO__SAT_PER_BYTE)

    def get_prices_per_unit_of_fee(self) -> data.PricesPerUnit:
        normal_fee_rate = self.get_normal_fee_rate()

        def _estimate_fee_or_default(number_of_blocks: int, ratio: Decimal) -> Decimal:
            sat_per_byte = None

            try:
                resp = self.restful.get(f"/api/v2/estimatefee/{number_of_blocks}")
                btc_per_kbytes = Decimal(resp.get("result") or 0)
                if btc_per_kbytes > 0:
                    sat_per_byte = btc_per_kbytes * BTC_PER_KBYTES__TO__SAT_PER_BYTE
            except Exception as e:
                logger.exception(f"Error in estimating fee: {e}")

            if sat_per_byte is None:
                sat_per_byte = round(normal_fee_rate * ratio)

            return max(MIN_SAT_PER_BYTE, sat_per_byte)

        fast_fee_rate = _estimate_fee_or_default(1, Decimal("1.5"))
        slow_fee_rate = _estimate_fee_or_default(5, Decimal("0.7"))

        blocktime_seconds = self.chain_info.blocktime_seconds or 600

        return data.PricesPerUnit(
            normal=data.EstimatedTimeOnPrice(price=int(normal_fee_rate), time=blocktime_seconds * 3),
            others=[
                data.EstimatedTimeOnPrice(price=int(fast_fee_rate), time=blocktime_seconds),
                data.EstimatedTimeOnPrice(price=int(slow_fee_rate), time=blocktime_seconds * 5),
            ],
        )

    def search_utxos_by_address(self, address: str) -> List[data.UTXO]:
        resp = self.restful.get(f"/api/v2/utxo/{address}", params=dict(confirmed=True))
        result = []

        if isinstance(resp, list):
            resp = (
                i
                for i in resp
                if i.get("confirmations", 0) > 0
                and i.get("coinbase", False) is False  # Only confirmed tx and matured coinbase
            )
            result.extend(data.UTXO(txid=i["txid"], vout=i["vout"], value=int(i["value"])) for i in resp)

        return result

    def search_txs_by_address(
        self,
        address: str,
        paginate: Optional[data.TxPaginate] = None,
    ) -> List[data.Transaction]:
        params = dict(details="txs")
        if paginate:
            params.update(_paging(paginate))

        resp = self.restful.get(f"/api/v2/address/{address}", params=params)
        return [_populate_transaction(i) for i in resp.get("transactions", ())]

    def search_txids_by_address(
        self,
        address: str,
        paginate: Optional[data.TxPaginate] = None,
    ) -> List[str]:
        params = dict(details="txids")
        if paginate:
            params.update(_paging(paginate))

        resp = self.restful.get(f"/api/v2/address/{address}", params=params)
        return [i for i in resp.get("txids", ())]
