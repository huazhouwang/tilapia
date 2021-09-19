from unittest import TestCase
from unittest.mock import Mock, patch

from wallet.lib.provider import data as provider_data
from wallet.lib.wallet.handlers import account


class TestAccountChainModelHandler(TestCase):
    def setUp(self) -> None:
        self.handler = account.AccountChainModelHandler()

        patch_coin_manager = patch("wallet.lib.wallet.handlers.account.coin_manager")
        patch_provider_manager = patch("wallet.lib.wallet.handlers.account.provider_manager")
        patch_daos = patch("wallet.lib.wallet.handlers.account.daos")

        self.fake_coin_manager = patch_coin_manager.start()
        self.fake_provider_manager = patch_provider_manager.start()
        self.fake_daos = patch_daos.start()

        self.addCleanup(patch_coin_manager.stop)
        self.addCleanup(patch_provider_manager.stop)
        self.addCleanup(patch_daos.stop)

        self.fake_coin_manager.get_related_coins.return_value = (
            Mock(code="eth"),
            Mock(code="eth", token_address=None),
            Mock(code="eth"),
        )
        self.fake_coin_manager.get_chain_info.return_value = Mock(chain_code="eth", chain_affinity="eth")

        self.fake_account = Mock(chain_code="eth", address="address1")
        self.fake_daos.account.query_first_account_by_wallet.return_value = self.fake_account
        self.fake_provider_manager.fill_unsigned_tx.side_effect = lambda chain_code, tx: tx.clone(
            fee_limit=21000, fee_price_per_unit=20
        )
        self.fake_provider_manager.verify_address.side_effect = lambda chain_code, address: Mock(
            normalized_address=address
        )

    def test_generate_unsigned_tx__meaningless_input(self):
        default_unsigned_tx = provider_data.UnsignedTx(fee_limit=21000, fee_price_per_unit=20)
        self.assertEqual(
            default_unsigned_tx,
            self.handler.generate_unsigned_tx(0, "eth"),
        )
        self.assertEqual(
            default_unsigned_tx,
            self.handler.generate_unsigned_tx(0, "eth", to_address="address2"),
        )
        self.assertEqual(2, self.fake_daos.account.query_first_account_by_wallet.call_count)
        self.assertEqual(2, self.fake_provider_manager.fill_unsigned_tx.call_count)

    def test_generate_unsigned_tx__main_coin(self):
        unsigned_tx = provider_data.UnsignedTx(
            inputs=[provider_data.TransactionInput(address="address1", value=1000)],
            outputs=[provider_data.TransactionOutput(address="address2", value=1000)],
            nonce=11,
            fee_limit=21000,
            fee_price_per_unit=20,
        )
        self.assertEqual(
            unsigned_tx, self.handler.generate_unsigned_tx(0, "eth", to_address="address2", value=1000, nonce=11)
        )
        self.fake_coin_manager.get_related_coins.assert_called_once_with("eth")
        self.fake_provider_manager.verify_address.assert_called_once_with("eth", "address2")
        self.fake_provider_manager.fill_unsigned_tx.assert_called_once_with(
            "eth", unsigned_tx.clone(fee_limit=None, fee_price_per_unit=None)
        )

    def test_generate_unsigned_tx__token(self):
        self.fake_coin_manager.get_related_coins.return_value = (
            Mock(code="eth"),
            Mock(code="eth_usdt", token_address="token1"),
            Mock(code="eth"),
        )
        self.fake_provider_manager.fill_unsigned_tx.side_effect = lambda chain_code, tx: tx.clone(
            fee_limit=10000, fee_price_per_unit=20
        )

        unsigned_tx = provider_data.UnsignedTx(
            inputs=[provider_data.TransactionInput(address="address1", value=1000, token_address="token1")],
            outputs=[provider_data.TransactionOutput(address="address2", value=1000, token_address="token1")],
            nonce=11,
            fee_limit=10000,
            fee_price_per_unit=20,
        )
        self.assertEqual(
            unsigned_tx, self.handler.generate_unsigned_tx(0, "eth_usdt", to_address="address2", value=1000, nonce=11)
        )
        self.fake_coin_manager.get_related_coins.assert_called_once_with("eth_usdt")
        self.fake_provider_manager.verify_address.assert_called_once_with("eth", "address2")
        self.fake_provider_manager.fill_unsigned_tx.assert_called_once_with(
            "eth", unsigned_tx.clone(fee_limit=None, fee_price_per_unit=None)
        )
