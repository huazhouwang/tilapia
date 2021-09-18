from unittest import TestCase
from unittest.mock import Mock, call, patch

from common.provider import data as provider_data
from common.utxo import data as utxo_data
from common.wallet.handlers import utxo


class TestUTXOChainModelHandler(TestCase):
    def setUp(self) -> None:
        self.handler = utxo.UTXOChainModelHandler()

        patch_coin_manager = patch("common.wallet.handlers.utxo.coin_manager")
        patch_provider_manager = patch("common.wallet.handlers.utxo.provider_manager")
        patch_utxo_manager = patch("common.wallet.handlers.utxo.utxo_manager")
        patch_daos = patch("common.wallet.handlers.utxo.daos")

        self.fake_coin_manager = patch_coin_manager.start()
        self.fake_provider_manager = patch_provider_manager.start()
        self.fake_utxo_manager = patch_utxo_manager.start()
        self.fake_daos = patch_daos.start()

        self.addCleanup(patch_coin_manager.stop)
        self.addCleanup(patch_provider_manager.stop)
        self.addCleanup(patch_utxo_manager.stop)
        self.addCleanup(patch_daos.stop)

        self.fake_coin_manager.get_related_coins.return_value = (
            Mock(code="btc"),
            Mock(code="btc"),
            Mock(code="btc"),
        )
        self.fake_coin_manager.get_chain_info.return_value = Mock(chain_code="btc", dust_threshold=546)

        self.fake_account = Mock(address="address1", bip44_path="m/44'/60'/0'/0/0")
        self.fake_daos.account.query_first_account_by_wallet.return_value = self.fake_account
        self.fake_provider_manager.fill_unsigned_tx.side_effect = lambda chain_code, tx: tx.clone(
            fee_limit=200, fee_price_per_unit=1
        )

    def test_generate_unsigned_tx__dual_token_model(self):
        self.fake_coin_manager.get_related_coins.return_value = (
            Mock(code="neo"),
            Mock(code="neo"),
            Mock(code="neo_gas"),
        )

        with self.assertRaisesRegex(Exception, "Dual token model isn't supported yet"):
            self.handler.generate_unsigned_tx(0, "neo")

        self.fake_coin_manager.get_related_coins.assert_called_once_with("neo")
        self.fake_coin_manager.get_chain_info.assert_not_called()

    def test_generate_unsigned_tx__meaningless_input(self):
        default_unsigned_tx = provider_data.UnsignedTx(fee_limit=200, fee_price_per_unit=1)

        self.assertEqual(default_unsigned_tx, self.handler.generate_unsigned_tx(0, "btc"))
        self.assertEqual(default_unsigned_tx, self.handler.generate_unsigned_tx(0, "btc", "address2"))
        self.assertEqual(default_unsigned_tx, self.handler.generate_unsigned_tx(0, "btc", "address2", value=0))
        self.assertEqual(default_unsigned_tx, self.handler.generate_unsigned_tx(0, "btc", "address2", value=545))
        self.assertEqual(4, self.fake_provider_manager.fill_unsigned_tx.call_count)

    def test_generate_unsigned_tx__not_enough_utxos_for_fee(self):
        self.fake_utxo_manager.choose_utxos.return_value = [Mock(address="address1", value=200, txid="txid1", vout=0)]

        with self.assertRaisesRegex(Exception, "Not enough utxos for fee"):
            self.handler.generate_unsigned_tx(0, "btc", "address2", value=1000)

    def test_generate_unsigned_tx__single_token_model(self):
        self.fake_utxo_manager.choose_utxos.return_value = [
            Mock(address="address1", value=1000, txid="txid1", vout=0),
            Mock(address="address1", value=1000, txid="txid1", vout=1),
            Mock(address="address1", value=1000, txid="txid1", vout=2),
        ]

        unsigned_tx = provider_data.UnsignedTx(
            inputs=[
                provider_data.TransactionInput(
                    address="address1",
                    value=1000,
                    utxo=provider_data.UTXO(txid="txid1", vout=0, value=1000),
                ),
                provider_data.TransactionInput(
                    address="address1",
                    value=1000,
                    utxo=provider_data.UTXO(txid="txid1", vout=1, value=1000),
                ),
                provider_data.TransactionInput(
                    address="address1",
                    value=1000,
                    utxo=provider_data.UTXO(txid="txid1", vout=2, value=1000),
                ),
            ],
            outputs=[
                provider_data.TransactionOutput(address="address2", value=2200),
                provider_data.TransactionOutput(
                    address="address1",
                    value=600,
                    payload={"is_change": True, "bip44_path": "m/44'/60'/0'/0/0"},
                ),
            ],
            fee_limit=200,
            fee_price_per_unit=1,
        )

        self.assertEqual(unsigned_tx, self.handler.generate_unsigned_tx(0, "btc", "address2", value=2200))
        self.fake_provider_manager.fill_unsigned_tx.assert_called_once_with(
            "btc",
            unsigned_tx.clone(
                outputs=[
                    provider_data.TransactionOutput(address="address2", value=2200),
                    provider_data.TransactionOutput(
                        address="address1",
                        value=800,
                        payload={"is_change": True, "bip44_path": "m/44'/60'/0'/0/0"},
                    ),
                ],
                fee_limit=0,
                fee_price_per_unit=0,
            ),
        )
        self.fake_utxo_manager.choose_utxos.assert_called_once_with(
            "btc", ["address1"], require_value=2200, status=utxo_data.UTXOStatus.SPENDABLE, min_value=546
        )
        self.fake_utxo_manager.refresh_utxos_by_address.assert_called_once_with("btc", "address1")
        self.fake_daos.account.query_first_account_by_wallet.assert_called_once_with(0)

    def test_generate_unsigned_tx__insufficient_utxos(self):
        self.fake_utxo_manager.choose_utxos.return_value = [
            Mock(address="address1", value=1000, txid="txid1", vout=0),
            Mock(address="address1", value=1000, txid="txid1", vout=1),
            Mock(address="address1", value=1000, txid="txid1", vout=2),
        ]

        unsigned_tx = provider_data.UnsignedTx(
            inputs=[
                provider_data.TransactionInput(
                    address="address1",
                    value=1000,
                    utxo=provider_data.UTXO(txid="txid1", vout=0, value=1000),
                ),
                provider_data.TransactionInput(
                    address="address1",
                    value=1000,
                    utxo=provider_data.UTXO(txid="txid1", vout=1, value=1000),
                ),
                provider_data.TransactionInput(
                    address="address1",
                    value=1000,
                    utxo=provider_data.UTXO(txid="txid1", vout=2, value=1000),
                ),
            ],
            outputs=[provider_data.TransactionOutput(address="address2", value=2800)],
            fee_limit=200,
            fee_price_per_unit=1,
        )

        self.assertEqual(unsigned_tx, self.handler.generate_unsigned_tx(0, "btc", "address2", value=3000))

        self.fake_provider_manager.fill_unsigned_tx.assert_called_once_with(
            "btc",
            unsigned_tx.clone(
                outputs=[provider_data.TransactionOutput(address="address2", value=3000)],
                fee_limit=0,
                fee_price_per_unit=0,
            ),
        )
        self.fake_utxo_manager.choose_utxos.assert_has_calls(
            [
                call("btc", ["address1"], require_value=3000, status=utxo_data.UTXOStatus.SPENDABLE, min_value=546),
                call("btc", ["address1"], require_value=3520, status=utxo_data.UTXOStatus.SPENDABLE, min_value=546),
            ]
        )
