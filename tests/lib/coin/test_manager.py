from typing import List
from unittest import TestCase
from unittest.mock import Mock, patch

from tilapia.lib.basic.orm import test_utils
from tilapia.lib.coin import daos, data, exceptions, loader, manager, models


def _order_coins(coins: List[data.CoinInfo]) -> List[data.CoinInfo]:
    return sorted(coins, key=lambda i: i.code)


@test_utils.cls_test_database(models.CoinModel)
class TestCoinManager(TestCase):
    _CACHED_CHAINS_DICT = loader.CHAINS_DICT.copy()
    _CACHED_COINS_DICT = loader.COINS_DICT.copy()

    @classmethod
    def setUpClass(cls) -> None:
        cls.chain_btc = Mock(chain_code="btc", chain_affinity="btc", fee_coin="btc")
        cls.chain_eth = Mock(chain_code="eth", chain_affinity="eth", fee_coin="eth")
        cls.chain_bsc = Mock(chain_code="bsc", chain_affinity="eth", fee_coin="bsc")
        cls.chain_ont = Mock(chain_code="ont", chain_affinity="ont", fee_coin="ont_ong")

        loader.CHAINS_DICT.clear()
        loader.CHAINS_DICT.update(
            {i.chain_code: i for i in (cls.chain_btc, cls.chain_eth, cls.chain_bsc, cls.chain_ont)}
        )

        cls.coin_btc = Mock(chain_code="btc", code="btc")
        cls.coin_eth = Mock(chain_code="eth", code="eth")
        cls.coin_eth_usdt = Mock(
            chain_code="eth", code="eth_usdt", token_address="0x52ce071bd9b1c4b00a0b92d298c512478cad67e7"
        )
        cls.coin_bsc = Mock(chain_code="bsc", code="bsc")

        cls.coin_ont = Mock(chain_code="ont", code="ont")
        cls.coin_ong = Mock(chain_code="ont", code="ont_ong", token_address="0x31")

        loader.COINS_DICT.clear()
        loader.COINS_DICT.update(
            {
                i.code: i
                for i in (cls.coin_btc, cls.coin_eth, cls.coin_eth_usdt, cls.coin_bsc, cls.coin_ont, cls.coin_ong)
            }
        )

    def setUp(self) -> None:
        self.coin_db_eth_usdc = data.CoinInfo(
            code="eth_usdc",
            chain_code="eth",
            name="USD Coin",
            symbol="USDC",
            decimals=6,
            token_address="0x52ce071bd9b1c4b00a0b92d298c512478cad67e8",
        )

        self.coin_db_eth_usdt = data.CoinInfo(
            code="eth_usdt",
            chain_code="eth",
            name="USDT",
            symbol="USDT",
            decimals=6,
            token_address="0x52ce071bd9b1c4b00a0b92d298c512478cad67e7",
        )

        self.coin_db_bsc_usdc = data.CoinInfo(
            code="bsc_usdc",
            chain_code="bsc",
            name="USD Coin",
            symbol="USDC",
            decimals=6,
            token_address="0x52ce071bd9b1c4b00a0b92d298c512478cad67e6",
        )

        daos.add_coin(
            self.coin_db_eth_usdc,
            self.coin_db_eth_usdt,  # invalid coin, would be hidden by local coin
            self.coin_db_bsc_usdc,
        )

    @classmethod
    def tearDownClass(cls) -> None:
        loader.CHAINS_DICT.clear()
        loader.CHAINS_DICT.update(cls._CACHED_CHAINS_DICT)

        loader.COINS_DICT.clear()
        loader.COINS_DICT.update(cls._CACHED_COINS_DICT)

    def test_get_chain_info(self):
        self.assertEqual(self.chain_btc, manager.get_chain_info("btc"))
        self.assertEqual(self.chain_eth, manager.get_chain_info("eth"))
        self.assertEqual(self.chain_bsc, manager.get_chain_info("bsc"))

        with self.assertRaisesRegex(exceptions.ChainNotFound, "heco"):
            manager.get_chain_info("heco")

    def test_get_coin_info(self):
        self.assertEqual(self.coin_btc, manager.get_coin_info("btc"))
        self.assertEqual(self.coin_eth, manager.get_coin_info("eth"))
        self.assertEqual(self.coin_eth_usdt, manager.get_coin_info("eth_usdt"))
        self.assertEqual(self.coin_bsc, manager.get_coin_info("bsc"))
        self.assertEqual(self.coin_db_eth_usdc, manager.get_coin_info("eth_usdc"))
        self.assertEqual(self.coin_db_bsc_usdc, manager.get_coin_info("bsc_usdc"))

        with self.assertRaisesRegex(exceptions.CoinNotFound, "eth_cc"):
            manager.get_coin_info("eth_cc")

        self.assertIsNone(manager.get_coin_info("eth_cc", nullable=True))

    def test_query_coins_by_codes(self):
        self.assertEqual(
            [
                self.coin_bsc,
                self.coin_db_bsc_usdc,
                self.coin_btc,
                self.coin_eth,
                self.coin_db_eth_usdc,
                self.coin_eth_usdt,
            ],
            _order_coins(manager.query_coins_by_codes(["btc", "eth", "eth_usdt", "bsc", "eth_usdc", "bsc_usdc"])),
        )

    def test_get_all_chains(self):
        self.assertEqual([self.chain_btc, self.chain_eth, self.chain_bsc, self.chain_ont], manager.get_all_chains())

    def test_get_all_coins(self):
        self.assertEqual(
            [
                self.coin_bsc,
                self.coin_db_bsc_usdc,
                self.coin_btc,
                self.coin_eth,
                self.coin_db_eth_usdc,
                self.coin_eth_usdt,
                self.coin_ont,
                self.coin_ong,
            ],
            _order_coins(manager.get_all_coins()),
        )

    def test_get_coins_by_chain(self):
        self.assertEqual([self.coin_btc], manager.get_coins_by_chain("btc"))
        self.assertEqual([self.coin_eth, self.coin_eth_usdt, self.coin_db_eth_usdc], manager.get_coins_by_chain("eth"))
        self.assertEqual([self.coin_bsc, self.coin_db_bsc_usdc], manager.get_coins_by_chain("bsc"))

    def test_get_related_coins(self):
        self.assertEqual((self.coin_btc, self.coin_btc, self.coin_btc), manager.get_related_coins("btc"))
        self.assertEqual((self.coin_eth, self.coin_eth, self.coin_eth), manager.get_related_coins("eth"))
        self.assertEqual((self.coin_eth, self.coin_eth_usdt, self.coin_eth), manager.get_related_coins("eth_usdt"))
        self.assertEqual((self.coin_bsc, self.coin_db_bsc_usdc, self.coin_bsc), manager.get_related_coins("bsc_usdc"))
        self.assertEqual((self.coin_ont, self.coin_ont, self.coin_ong), manager.get_related_coins("ont"))
        self.assertEqual((self.coin_ont, self.coin_ong, self.coin_ong), manager.get_related_coins("ont_ong"))

    @patch("tilapia.lib.coin.manager.daos.add_coin")
    @patch("tilapia.lib.coin.manager.daos.update_coin_info")
    def test_add_coin(self, fake_update_coin_info, fake_add_coin):
        with self.subTest("Add coin that already exists in the local list"):
            self.assertEqual(
                "eth_usdt", manager.add_coin("eth", "0x52ce071bd9b1c4b00a0b92d298c512478cad67e7", "USDT", 6)
            )
            fake_add_coin.assert_not_called()
            fake_update_coin_info.assert_not_called()

        with self.subTest("Add coin that already exists in the db"):
            self.assertEqual(
                "eth_usdc",
                manager.add_coin(
                    "eth", "0x52ce071bd9b1c4b00a0b92d298c512478cad67e8", "USDC", 6, name="New USD Coin", icon="new icon"
                ),
            )
            fake_add_coin.assert_not_called()
            fake_update_coin_info.assert_called_once_with("eth_usdc", name="New USD Coin", icon="new icon")
            fake_update_coin_info.reset_mock()

        with self.subTest("Add coin with duplicated symbol"):
            self.assertEqual(
                "eth_usdc_0x52ce",
                manager.add_coin(
                    "eth", "0x52ce071bd9b1c4b00a0b92d298c512478cad67e5", "USDC", 6, name="New USD Coin", icon="new icon"
                ),
            )
            fake_add_coin.assert_called_once_with(
                data.CoinInfo(
                    code="eth_usdc_0x52ce",
                    chain_code="eth",
                    token_address="0x52ce071bd9b1c4b00a0b92d298c512478cad67e5",
                    symbol="USDC",
                    decimals=6,
                    name="New USD Coin",
                    icon="new icon",
                )
            )
            fake_update_coin_info.assert_not_called()
            fake_add_coin.reset_mock()

        with self.subTest("Add coin in most cases"):
            self.assertEqual("eth_cc", manager.add_coin("eth", "0x52ce071bd9b1c4b00a0b92d298c512478cad67e5", "CC", 18))

            fake_add_coin.assert_called_once_with(
                data.CoinInfo(
                    code="eth_cc",
                    chain_code="eth",
                    token_address="0x52ce071bd9b1c4b00a0b92d298c512478cad67e5",
                    symbol="CC",
                    decimals=18,
                    name="CC",
                    icon=None,
                )
            )
            fake_update_coin_info.assert_not_called()
            fake_add_coin.reset_mock()

    def test_query_coins_by_token_addresses(self):
        self.assertEqual(
            [self.coin_eth_usdt, self.coin_db_eth_usdc],
            manager.query_coins_by_token_addresses(
                "eth",
                [
                    "0x52ce071bd9b1c4b00a0b92d298c512478cad67e8",
                    "0x52ce071bd9b1c4b00a0b92d298c512478cad67e7",
                    "0x52ce071bd9b1c4b00a0b92d298c512478cad67e5",
                ],
            ),
        )
        self.assertEqual(
            [self.coin_db_bsc_usdc],
            manager.query_coins_by_token_addresses("bsc", ["0x52ce071bd9b1c4b00a0b92d298c512478cad67e6"]),
        )
        self.assertEqual([self.coin_ong], manager.query_coins_by_token_addresses("ont", ["0x31"]))

    def test_get_coin_by_token_address(self):
        with self.subTest("get coin by token address as expected"):
            self.assertEqual(
                self.coin_db_eth_usdc,
                manager.get_coin_by_token_address("eth", "0x52ce071bd9b1c4b00a0b92d298c512478cad67e8"),
            )

        with self.subTest("get coin by token address but nothing found"):
            with self.assertRaisesRegex(
                exceptions.CoinNotFoundByTokenAddress, "0x52ce071bd9b1c4b00a0b92d298c512478cad67e5"
            ):
                manager.get_coin_by_token_address("eth", "0x52ce071bd9b1c4b00a0b92d298c512478cad67e5")

        with self.subTest("automatically add token address"):
            with patch(
                "tilapia.lib.coin.manager.provider_manager.get_token_info_by_address"
            ) as fake_get_token_info_by_address:
                fake_get_token_info_by_address.return_value = ("CC", "Chain Coin", 18)
                self.assertEqual(
                    data.CoinInfo(
                        code="eth_cc",
                        chain_code="eth",
                        token_address="0x52ce071bd9b1c4b00a0b92d298c512478cad67e5",
                        symbol="CC",
                        decimals=18,
                        name="Chain Coin",
                        icon=None,
                    ),
                    manager.get_coin_by_token_address(
                        "eth", "0x52ce071bd9b1c4b00a0b92d298c512478cad67e5", add_if_missing=True
                    ),
                )
