import datetime
import decimal
from unittest import TestCase
from unittest.mock import Mock, call, patch

import peewee

from tilapia.lib.basic.orm import test_utils
from tilapia.lib.coin import data as coin_data
from tilapia.lib.provider import data as provider_data
from tilapia.lib.provider import exceptions as provider_exceptions
from tilapia.lib.transaction import daos, data, manager, models


@test_utils.cls_test_database(models.TxAction)
class TestTransactionManager(TestCase):
    @patch("tilapia.lib.transaction.manager.coin_manager")
    @patch("tilapia.lib.transaction.manager.provider_manager")
    def test_update_pending_actions(self, fake_provider_manager, fake_coin_manager):
        # prepare data
        daos.bulk_create(
            [
                daos.new_action(
                    txid="txid_a",
                    status=data.TxActionStatus.PENDING,
                    chain_code="eth",
                    coin_code="eth",
                    value=decimal.Decimal(0),
                    from_address="address_a",
                    to_address="contract_a",
                    fee_limit=decimal.Decimal(1000),
                    fee_price_per_unit=decimal.Decimal(20),
                    nonce=11,
                    raw_tx="",
                ),
                daos.new_action(
                    txid="txid_a",
                    status=data.TxActionStatus.PENDING,
                    chain_code="eth",
                    coin_code="eth_usdt",
                    value=decimal.Decimal(10),
                    from_address="address_a",
                    to_address="address_b",
                    fee_limit=decimal.Decimal(1000),
                    fee_price_per_unit=decimal.Decimal(20),
                    index=1,
                    raw_tx="",
                ),
                daos.new_action(
                    txid="txid_b",
                    status=data.TxActionStatus.PENDING,
                    chain_code="bsc",
                    coin_code="bsc",
                    value=decimal.Decimal(3),
                    from_address="address_b",
                    to_address="address_c",
                    fee_limit=decimal.Decimal(1000),
                    fee_price_per_unit=decimal.Decimal(20),
                    nonce=3,
                    raw_tx="",
                ),
                daos.new_action(
                    txid="txid_c",
                    status=data.TxActionStatus.PENDING,
                    chain_code="heco",
                    coin_code="heco",
                    value=decimal.Decimal(4),
                    from_address="address_c",
                    to_address="address_b",
                    fee_limit=decimal.Decimal(1000),
                    fee_price_per_unit=decimal.Decimal(20),
                    nonce=3,
                    raw_tx="",
                ),
                daos.new_action(
                    txid="txid_d",
                    status=data.TxActionStatus.PENDING,
                    chain_code="eth",
                    coin_code="eth",
                    value=decimal.Decimal(10),
                    from_address="address_a",
                    to_address="address_b",
                    fee_limit=decimal.Decimal(1000),
                    fee_price_per_unit=decimal.Decimal(10),
                    nonce=11,
                    raw_tx="",
                ),
                daos.new_action(
                    txid="txid_e",
                    status=data.TxActionStatus.PENDING,
                    chain_code="eth",
                    coin_code="eth",
                    value=decimal.Decimal(11),
                    from_address="address_a",
                    to_address="address_b",
                    fee_limit=decimal.Decimal(1000),
                    fee_price_per_unit=decimal.Decimal(15),
                    nonce=11,
                    raw_tx="",
                ),
            ]
        )

        # Adjust the created time of the transaction to 3 days ago
        tx_bsc: models.TxAction = models.TxAction.get_or_none(txid="txid_b")
        models.TxAction.update(created_time=datetime.datetime.now() - datetime.timedelta(days=3)).where(
            models.TxAction.id == tx_bsc.id
        ).execute()

        fake_coin_manager.get_chain_info.return_value = Mock(
            chain_model=coin_data.ChainModel.ACCOUNT, nonce_supported=True
        )

        def _fake_get_transaction_by_txid(chain_code, txid):
            if txid not in ("txid_a", "txid_b", "txid_c"):
                raise provider_exceptions.TransactionNotFound(txid)
            return {
                "eth": provider_data.Transaction(
                    txid="txid_a",
                    status=provider_data.TransactionStatus.CONFIRM_SUCCESS,
                    fee=provider_data.TransactionFee(limit=1000, used=900, price_per_unit=20),
                    block_header=provider_data.BlockHeader(
                        block_hash="block_a", block_number=1001, block_time=1600000000, confirmations=3
                    ),
                ),
                "bsc": provider_data.Transaction(
                    txid="txid_b",
                    status=provider_data.TransactionStatus.PENDING,
                ),
                "heco": provider_data.Transaction(
                    txid="txid_c",
                    status=provider_data.TransactionStatus.CONFIRM_REVERTED,
                    fee=provider_data.TransactionFee(limit=1000, used=1000, price_per_unit=20),
                    block_header=provider_data.BlockHeader(
                        block_hash="block_c", block_number=1010, block_time=1600000001
                    ),
                ),
            }.get(chain_code)

        fake_provider_manager.get_transaction_by_txid.side_effect = _fake_get_transaction_by_txid

        manager.update_pending_actions()

        txns = list(models.TxAction.select().order_by(models.TxAction.id.asc()))
        self.assertEqual(
            [
                {
                    "id": 1,
                    "txid": "txid_a",
                    "chain_code": "eth",
                    "coin_code": "eth",
                    "status": data.TxActionStatus.CONFIRM_SUCCESS,
                    "fee_used": decimal.Decimal(900),
                    "block_number": 1001,
                    "block_hash": "block_a",
                    "block_time": 1600000000,
                },
                {
                    "id": 2,
                    "txid": "txid_a",
                    "chain_code": "eth",
                    "coin_code": "eth_usdt",
                    "status": data.TxActionStatus.CONFIRM_SUCCESS,
                    "fee_used": decimal.Decimal(900),
                    "block_number": 1001,
                    "block_hash": "block_a",
                    "block_time": 1600000000,
                },
                {
                    "id": 3,
                    "txid": "txid_b",
                    "chain_code": "bsc",
                    "coin_code": "bsc",
                    "status": data.TxActionStatus.UNKNOWN,
                    "fee_used": decimal.Decimal(0),
                    "block_number": None,
                    "block_hash": None,
                    "block_time": None,
                },
                {
                    "id": 4,
                    "txid": "txid_c",
                    "chain_code": "heco",
                    "coin_code": "heco",
                    "status": data.TxActionStatus.CONFIRM_REVERTED,
                    "fee_used": decimal.Decimal(1000),
                    "block_number": 1010,
                    "block_hash": "block_c",
                    "block_time": 1600000001,
                },
                {
                    "id": 5,
                    "txid": "txid_d",
                    "chain_code": "eth",
                    "coin_code": "eth",
                    "status": data.TxActionStatus.REPLACED,
                    "fee_used": decimal.Decimal(0),
                    "block_number": None,
                    "block_hash": None,
                    "block_time": None,
                },
                {
                    "id": 6,
                    "txid": "txid_e",
                    "chain_code": "eth",
                    "coin_code": "eth",
                    "status": data.TxActionStatus.REPLACED,
                    "fee_used": decimal.Decimal(0),
                    "block_number": None,
                    "block_hash": None,
                    "block_time": None,
                },
            ],
            [
                {
                    "id": i.id,
                    "txid": i.txid,
                    "chain_code": i.chain_code,
                    "coin_code": i.coin_code,
                    "status": i.status,
                    "fee_used": i.fee_used,
                    "block_number": i.block_number,
                    "block_hash": i.block_hash,
                    "block_time": i.block_time,
                }
                for i in txns
            ],
        )
        fake_provider_manager.get_transaction_by_txid.assert_has_calls(
            [
                call("bsc", "txid_b"),
                call("eth", "txid_a"),
                call("eth", "txid_d"),
                call("eth", "txid_e"),
                call("heco", "txid_c"),
            ],
            any_order=True,
        )

    def test_unique_indexes_of_tx_action(self):
        models.TxAction.create(
            txid="txid_a",
            status=data.TxActionStatus.CONFIRM_SUCCESS,
            chain_code="eth",
            coin_code="eth",
            value=decimal.Decimal(0),
            from_address="address_a",
            to_address="contract_a",
            fee_limit=decimal.Decimal(1000),
            fee_price_per_unit=decimal.Decimal(20),
            raw_tx="",
            nonce=0,
            index=0,
        )

        with self.assertRaisesRegex(
            peewee.IntegrityError, "UNIQUE constraint failed: txaction.txid, txaction.coin_code, txaction.index"
        ):
            models.TxAction.create(
                txid="txid_a",
                status=data.TxActionStatus.CONFIRM_SUCCESS,
                chain_code="eth",
                coin_code="eth",
                value=decimal.Decimal(0),
                from_address="address_a",
                to_address="contract_a",
                fee_limit=decimal.Decimal(1000),
                fee_price_per_unit=decimal.Decimal(20),
                raw_tx="",
                nonce=0,
                index=0,
            )

    @patch("tilapia.lib.transaction.manager.provider_manager")
    @patch("tilapia.lib.transaction.manager.coin_manager")
    @patch("tilapia.lib.transaction.manager.time")
    def test_query_actions_by_address(self, fake_time, fake_coin_manager, fake_provider_manager):
        fake_coin_manager.get_chain_info.return_value = Mock(chain_model=coin_data.ChainModel.ACCOUNT)
        fake_coin_manager.get_coin_info.return_value = Mock(code="eth")
        fake_coin_manager.query_coins_by_token_addresses.return_value = []
        fake_provider_manager.verify_address.side_effect = lambda chain_code, address: Mock(normalized_address=address)

        def _build_action_by_pattern(txid: str, **kwargs):
            pattern = dict(
                chain_code="eth",
                coin_code="eth",
                value=decimal.Decimal(10),
                from_address="address_a",
                to_address="address_b",
                fee_limit=decimal.Decimal(1000),
                fee_price_per_unit=decimal.Decimal(20),
                raw_tx="",
            )
            _data = pattern.copy()
            _data.update(kwargs)
            _data["txid"] = txid
            return daos.new_action(**_data)

        # 1. prepare existing actions
        daos.bulk_create(
            [
                _build_action_by_pattern(
                    "txid_from_a_100",
                    status=data.TxActionStatus.PENDING,
                    nonce=100,
                    created_time=datetime.datetime.utcfromtimestamp(1620000002),
                ),
                _build_action_by_pattern(
                    "txid_from_a_99",
                    status=data.TxActionStatus.PENDING,
                    nonce=99,
                    created_time=datetime.datetime.utcfromtimestamp(1620000001),
                ),
            ]
        )
        self.assertEqual(2, models.TxAction.select().count())

        # 2. prepare fake txs
        send_from_a = [
            provider_data.Transaction(
                txid=f"txid_from_a_{i}",
                status=provider_data.TransactionStatus.CONFIRM_SUCCESS,
                inputs=[provider_data.TransactionInput(address="address_a", value=10)],
                outputs=[provider_data.TransactionOutput(address="address_b", value=10)],
                fee=provider_data.TransactionFee(limit=1000, used=900, price_per_unit=20),
                nonce=i,
            )
            for i in range(100)
        ]
        send_to_a = [
            provider_data.Transaction(
                txid=f"txid_to_a_{i}",
                status=provider_data.TransactionStatus.CONFIRM_SUCCESS,
                inputs=[provider_data.TransactionInput(address=f"address_{i}", value=10)],
                outputs=[provider_data.TransactionOutput(address="address_a", value=10)],
                fee=provider_data.TransactionFee(limit=1000, used=900, price_per_unit=20),
                nonce=0,
            )
            for i in range(200)
        ]
        txs = send_to_a[:100] + send_from_a + send_to_a[100:]

        for index, tx in enumerate(txs):
            tx.block_header = provider_data.BlockHeader(
                block_hash=f"block_{index}", block_number=index, block_time=1610000000 + index
            )
        txs.sort(key=lambda i: i.block_header.block_number, reverse=True)

        txids = [i.txid for i in txs]
        txids.remove("txid_from_a_99")
        txids = ["txid_from_a_100", "txid_from_a_99", *txids]

        fake_provider_manager.search_txs_by_address.side_effect = lambda chain_code, address, paginate: [
            i
            for i in txs
            if (not paginate.start_block_number or i.block_header.block_number >= paginate.start_block_number)
            and (not paginate.end_block_number or i.block_header.block_number <= paginate.end_block_number)
        ][: paginate.items_per_page]

        # 2. fetch the first page
        fake_time.time.return_value = 1620000000
        local_actions = manager.query_actions_by_address("eth", "eth", "address_a")
        self.assertEqual(
            txids[:20],
            [i.txid for i in local_actions],
        )
        self.assertEqual(201, models.TxAction.select().count())
        fake_time.time.assert_called_once()
        fake_provider_manager.verify_address.assert_called_once_with("eth", "address_a")
        fake_provider_manager.search_txs_by_address.assert_called_once_with(
            "eth", "address_a", paginate=provider_data.TxPaginate(items_per_page=200)
        )
        fake_time.time.reset_mock()
        fake_provider_manager.verify_address.reset_mock()
        fake_provider_manager.search_txs_by_address.reset_mock()

        # 3. fetch the following 9 pages without network
        for page_number in range(2, 11):
            local_actions.extend(manager.query_actions_by_address("eth", "eth", "address_a", page_number=page_number))

        self.assertEqual(201, models.TxAction.select().count())
        self.assertEqual(200, len(local_actions))
        self.assertEqual(txids[:200], [i.txid for i in local_actions])
        self.assertEqual(9, fake_provider_manager.verify_address.call_count)
        fake_time.time.assert_not_called()
        fake_provider_manager.search_txs_by_address.assert_not_called()

        # 4. fetch the remaining txs
        local_actions.extend(manager.query_actions_by_address("eth", "eth", "address_a", page_number=11))

        self.assertEqual(301, models.TxAction.select().count())
        fake_time.time.assert_not_called()
        fake_provider_manager.search_txs_by_address.assert_called_once_with(
            "eth", "address_a", paginate=provider_data.TxPaginate(end_block_number=100, items_per_page=200)
        )
        fake_provider_manager.search_txs_by_address.reset_mock()

        # 5. fetch the following 4 pages without network
        for page_number in range(12, 16):
            local_actions.extend(manager.query_actions_by_address("eth", "eth", "address_a", page_number=page_number))

        self.assertEqual(301, models.TxAction.select().count())
        self.assertEqual(300, len(local_actions))
        self.assertEqual(txids[:300], [i.txid for i in local_actions])
        fake_time.time.assert_not_called()
        fake_provider_manager.search_txs_by_address.assert_not_called()
        fake_provider_manager.search_txs_by_address.reset_mock()

        # 6. fetch the final page
        local_actions.extend(manager.query_actions_by_address("eth", "eth", "address_a", page_number=16))
        self.assertEqual(301, len(local_actions))
        self.assertEqual(txids, [i.txid for i in local_actions])
        fake_time.time.assert_not_called()
        fake_provider_manager.search_txs_by_address.assert_called_once_with(
            "eth", "address_a", paginate=provider_data.TxPaginate(end_block_number=0, items_per_page=200)
        )
        fake_provider_manager.search_txs_by_address.reset_mock()

        # 7. suppose there are new data after a while, prepare new data
        send_from_a = [
            provider_data.Transaction(
                txid=f"txid_from_a_{i}",
                status=provider_data.TransactionStatus.CONFIRM_SUCCESS,
                inputs=[provider_data.TransactionInput(address="address_a", value=10)],
                outputs=[provider_data.TransactionOutput(address="address_b", value=10)],
                fee=provider_data.TransactionFee(limit=1000, used=900, price_per_unit=20),
                nonce=i,
            )
            for i in range(100, 300)
        ]
        send_to_a = [
            provider_data.Transaction(
                txid=f"txid_to_a_{i}",
                status=provider_data.TransactionStatus.CONFIRM_SUCCESS,
                inputs=[provider_data.TransactionInput(address=f"address_{i}", value=10)],
                outputs=[provider_data.TransactionOutput(address="address_a", value=10)],
                fee=provider_data.TransactionFee(limit=1000, used=900, price_per_unit=20),
                nonce=0,
            )
            for i in range(200, 300)
        ]

        new_txs = send_from_a[:100] + send_to_a + send_from_a[100:]

        for index, tx in enumerate(new_txs):
            tx.block_header = provider_data.BlockHeader(
                block_hash=f"block_{index}", block_number=index + 300, block_time=1640000000 + index
            )

        new_txs.sort(key=lambda i: i.block_header.block_number, reverse=True)
        new_txids = [i.txid for i in new_txs]
        new_txs.extend(txs)
        txs.clear()
        txs.extend(new_txs)
        txs.sort(key=lambda i: i.block_header.block_number, reverse=True)

        new_txids.remove("txid_from_a_100")
        txids = [*new_txids, *txids]

        # 8. fetch the first page again
        fake_time.time.return_value = 1640000000
        local_actions = manager.query_actions_by_address("eth", "eth", "address_a")
        self.assertEqual(
            txids[:20],
            [i.txid for i in local_actions],
        )
        self.assertEqual(501, models.TxAction.select().count())
        fake_time.time.assert_called_once()
        fake_provider_manager.search_txs_by_address.assert_called_once_with(
            "eth", "address_a", paginate=provider_data.TxPaginate(start_block_number=298, items_per_page=200)
        )
        fake_time.time.reset_mock()
        fake_provider_manager.verify_address.reset_mock()
        fake_provider_manager.search_txs_by_address.reset_mock()

        # 9. fetch the following 9 pages without network
        for page_number in range(2, 11):
            local_actions.extend(manager.query_actions_by_address("eth", "eth", "address_a", page_number=page_number))

        self.assertEqual(501, models.TxAction.select().count())
        self.assertEqual(200, len(local_actions))
        self.assertEqual(txids[:200], [i.txid for i in local_actions])
        fake_time.time.assert_not_called()
        fake_provider_manager.search_txs_by_address.assert_not_called()

        # 10. fetch the remaining txs between 298 to 400
        local_actions.extend(manager.query_actions_by_address("eth", "eth", "address_a", page_number=11))

        self.assertEqual(600, models.TxAction.select().count())
        self.assertEqual(txids[:220], [i.txid for i in local_actions])
        fake_time.time.assert_not_called()
        fake_provider_manager.search_txs_by_address.assert_called_once_with(
            "eth",
            "address_a",
            paginate=provider_data.TxPaginate(start_block_number=298, end_block_number=400, items_per_page=200),
        )
        fake_provider_manager.search_txs_by_address.reset_mock()

        # 11. fetch the following all pages
        for page_number in range(12, 31):
            local_actions.extend(manager.query_actions_by_address("eth", "eth", "address_a", page_number=page_number))

        self.maxDiff = None
        self.assertEqual(600, models.TxAction.select().count())
        self.assertEqual(600, len(local_actions))
        self.assertEqual(txids, [i.txid for i in local_actions])
        fake_time.time.assert_not_called()
        fake_provider_manager.search_txs_by_address.assert_not_called()

        # 12. nothing anymore
        local_actions.extend(manager.query_actions_by_address("eth", "eth", "address_a", page_number=31))
        self.assertEqual(600, models.TxAction.select().count())
        self.assertEqual(600, len(local_actions))
        fake_provider_manager.search_txs_by_address.assert_called_once_with(
            "eth",
            "address_a",
            paginate=provider_data.TxPaginate(end_block_number=0, page_number=1, items_per_page=200),
        )
        fake_provider_manager.search_txs_by_address.reset_mock()

        # 13. check searching_address_as argument
        fake_time.time.return_value = 1650000000
        self.assertEqual(
            [i for i in txids if "from" in i],
            [
                i.txid
                for i in manager.query_actions_by_address(
                    "eth", "eth", "address_a", searching_address_as="sender", items_per_page=600
                )
            ],
        )
        fake_provider_manager.search_txs_by_address.assert_has_calls(
            [
                call(
                    "eth",
                    "address_a",
                    paginate=provider_data.TxPaginate(start_block_number=598, page_number=1, items_per_page=200),
                ),
                call(
                    "eth",
                    "address_a",
                    paginate=provider_data.TxPaginate(end_block_number=0, page_number=1, items_per_page=400),
                ),
            ]
        )
        fake_provider_manager.search_txs_by_address.reset_mock()

        fake_time.time.return_value = 1660000000
        self.assertEqual(
            [i for i in txids if "to" in i],
            [
                i.txid
                for i in manager.query_actions_by_address(
                    "eth", "eth", "address_a", searching_address_as="receiver", items_per_page=600
                )
            ],
        )
        fake_provider_manager.search_txs_by_address.assert_has_calls(
            [
                call(
                    "eth",
                    "address_a",
                    paginate=provider_data.TxPaginate(start_block_number=598, page_number=1, items_per_page=200),
                ),
                call(
                    "eth",
                    "address_a",
                    paginate=provider_data.TxPaginate(end_block_number=0, page_number=1, items_per_page=400),
                ),
            ]
        )

    @patch("tilapia.lib.transaction.manager.provider_manager")
    @patch("tilapia.lib.transaction.manager.coin_manager")
    @patch("tilapia.lib.transaction.manager.time")
    def test_query_actions_by_address_check_max_times(self, fake_time, fake_coin_manager, fake_provider_manager):
        fake_time.time.return_value = 1610000000
        fake_coin_manager.get_chain_info.return_value = Mock(chain_model=coin_data.ChainModel.ACCOUNT)
        fake_coin_manager.get_coin_info.return_value = Mock(code="eth")
        fake_coin_manager.query_coins_by_token_addresses.return_value = []
        fake_provider_manager.verify_address.side_effect = lambda chain_code, address: Mock(normalized_address=address)

        txs = [
            provider_data.Transaction(
                txid=f"txid_from_a_{i}",
                status=provider_data.TransactionStatus.CONFIRM_SUCCESS,
                inputs=[provider_data.TransactionInput(address="address_a", value=10)],
                outputs=[provider_data.TransactionOutput(address="address_b", value=10)],
                fee=provider_data.TransactionFee(limit=1000, used=900, price_per_unit=20),
                block_header=provider_data.BlockHeader(
                    block_number=1000 + i, block_time=1600000000 + i, block_hash=f"block_{i}"
                ),
                nonce=i,
            )
            for i in range(10)
        ]
        fake_provider_manager.search_txs_by_address.side_effect = lambda *args, **kwargs: [txs.pop()] if txs else []

        local_actions = manager.query_actions_by_address("eth", "eth", "address_a")
        self.assertEqual(["txid_from_a_9", "txid_from_a_8", "txid_from_a_7"], [i.txid for i in local_actions])
        fake_time.time.assert_called_once()
        fake_provider_manager.search_txs_by_address.assert_has_calls(
            [
                call("eth", "address_a", paginate=provider_data.TxPaginate(items_per_page=200)),
                call("eth", "address_a", paginate=provider_data.TxPaginate(end_block_number=1009, items_per_page=400)),
                call("eth", "address_a", paginate=provider_data.TxPaginate(end_block_number=1008, items_per_page=800)),
            ]
        )
