import decimal
from unittest import TestCase
from unittest.mock import Mock, call, patch

from wallet.lib.basic.orm import test_utils
from wallet.lib.price import daos, data, manager, models


@test_utils.cls_test_database(models.Price)
class TestPriceManager(TestCase):
    @patch("wallet.lib.price.manager._registry")
    @patch("wallet.lib.price.manager.coin_manager")
    @patch("wallet.lib.price.manager.daos")
    def test_pricing(self, fake_daos, fake_coin_manager, fake_registry):
        with self.subTest("Pricing all coins"):
            fake_coins = [Mock(code="btc"), Mock(code="eth")]
            fake_coin_manager.get_all_coins.return_value = fake_coins

            fake_channel = Mock()
            fake_channel.pricing.return_value = [
                data.YieldedPrice("btc", 123456, "usd"),
                data.YieldedPrice("eth", 12345, "usd"),
            ]
            fake_registry.items.return_value = [(data.Channel.CGK, lambda: fake_channel)]

            manager.pricing()

            fake_coin_manager.get_all_coins.assert_called_once()
            fake_coin_manager.query_coins_by_codes.assert_not_called()
            fake_daos.create_or_update.assert_has_calls(
                [
                    call(
                        coin_code="btc",
                        unit="usd",
                        channel=data.Channel.CGK,
                        price=123456,
                    ),
                    call(
                        coin_code="eth",
                        unit="usd",
                        channel=data.Channel.CGK,
                        price=12345,
                    ),
                ]
            )
            fake_coin_manager.get_all_coins.reset_mock()
            fake_daos.create_or_update.reset_mock()

        with self.subTest("Price specific coins"):
            fake_coin_manager.query_coins_by_codes.return_value = []
            manager.pricing(["btc", "eth", "bsc"])
            fake_coin_manager.query_coins_by_codes.assert_called_once_with(["btc", "eth", "bsc"])
            fake_coin_manager.get_all_coins.assert_not_called()
            fake_daos.create_or_update.assert_not_called()

    @patch("wallet.lib.price.manager.coin_manager")
    def test_get_last_price(self, fake_coin_manager):
        # create fake pricing table
        # btc: 120000 usd,
        # eth: 15000 usd, eth_cc: 15
        # bsc: 120 usd, bsc_cc: 12
        daos.create_or_update("btc", "usd", data.Channel.CGK, decimal.Decimal(120000))
        daos.create_or_update("btc", "cny", data.Channel.CGK, decimal.Decimal(780000))
        daos.create_or_update("eth", "usd", data.Channel.CGK, decimal.Decimal(15000))
        daos.create_or_update("eth_cc", "eth", data.Channel.CGK, decimal.Decimal(0.001))
        daos.create_or_update("bsc", "btc", data.Channel.CGK, decimal.Decimal(0.001))
        daos.create_or_update("bsc_cc", "bsc", data.Channel.CGK, decimal.Decimal(0.1))

        fake_coin_manager.get_coin_info.side_effect = lambda code, nullable: {
            "btc": Mock(code="btc", chain_code="btc"),
            "eth": Mock(code="eth", chain_code="eth"),
            "eth_cc": Mock(code="eth_cc", chain_code="eth"),
            "bsc": Mock(code="bsc", chain_code="bsc"),
            "bsc_cc": Mock(code="bsc_cc", chain_code="bsc"),
        }.get(code)

        self.assertEqual(120000, manager.get_last_price("btc", "usd"))
        self.assertEqual(15000, manager.get_last_price("eth", "usd"))
        self.assertEqual(15, manager.get_last_price("eth_cc", "usd"))
        self.assertEqual(120, manager.get_last_price("bsc", "usd"))
        self.assertEqual(12, manager.get_last_price("bsc_cc", "usd"))
        self.assertEqual(780000, manager.get_last_price("btc", "cny"))
        self.assertEqual(0, manager.get_last_price("eth", "cny"))
        self.assertEqual(780, manager.get_last_price("bsc", "cny"))
        self.assertEqual(78, manager.get_last_price("bsc_cc", "cny"))
        self.assertEqual(0, manager.get_last_price("bsc_abc", "usd"))
        self.assertEqual(111, manager.get_last_price("bsc_abc", "usd", default=decimal.Decimal(111)))
