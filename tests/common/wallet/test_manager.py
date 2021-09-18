import datetime
import decimal
from unittest import TestCase
from unittest.mock import Mock, call, patch

from common.basic import bip44, cipher
from common.basic.orm import test_utils
from common.coin import data as coin_data
from common.coin import models as coin_models
from common.provider import data as provider_data
from common.secret import data as secret_data
from common.secret import models as secret_models
from common.transaction import data as transaction_data
from common.transaction import manager as transaction_manager
from common.transaction import models as transaction_models
from common.utxo import models as utxo_models
from common.wallet import daos as wallet_daos
from common.wallet import data as wallet_data
from common.wallet import exceptions as wallet_exceptions
from common.wallet import manager as wallet_manager
from common.wallet import models as wallet_models


@test_utils.cls_test_database(
    wallet_models.WalletModel,
    wallet_models.AccountModel,
    wallet_models.AssetModel,
    secret_models.PubKeyModel,
    secret_models.SecretKeyModel,
    transaction_models.TxAction,
    coin_models.CoinModel,
    utxo_models.UTXO,
    utxo_models.WhoSpent,
)
class TestWalletManager(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.password = "moon"
        cls.mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
        cls.passphrase = "OneKey"

    def setUp(self) -> None:
        # Add needed mock data for these tests.
        # TODO: this should be remove when the tests are changed to real unit tests, now these tests are more functional.
        chains = [
            coin_data.ChainInfo(
                chain_code="btc",
                fee_coin="btc",
                chain_model=coin_data.ChainModel.UTXO,
                shortname="BTC",
                name="Bitcoin",
                curve=secret_data.CurveEnum.SECP256K1,
                chain_affinity="btc",
                bip44_coin_type=0,
                bip44_target_level=bip44.BIP44Level.ADDRESS_INDEX,
                bip44_auto_increment_level=bip44.BIP44Level.ACCOUNT,
                bip44_last_hardened_level=bip44.BIP44Level.ACCOUNT,
                default_address_encoding="P2WPKH-P2SH",
                bip44_purpose_options={"P2PKH": 44, "P2WPKH-P2SH": 49, "P2WPKH": 84},
                dust_threshold=546,
            ),
            coin_data.ChainInfo(
                chain_code="eth",
                fee_coin="eth",
                chain_model=coin_data.ChainModel.ACCOUNT,
                shortname="ETH",
                name="Ethereum",
                curve=secret_data.CurveEnum.SECP256K1,
                chain_affinity="eth",
                bip44_coin_type=60,
                bip44_target_level=bip44.BIP44Level.ADDRESS_INDEX,
                bip44_auto_increment_level=bip44.BIP44Level.ADDRESS_INDEX,
                bip44_last_hardened_level=bip44.BIP44Level.ACCOUNT,
            ),
            coin_data.ChainInfo(
                chain_code="bsc",
                fee_coin="bsc",
                chain_model=coin_data.ChainModel.ACCOUNT,
                shortname="BSC",
                name="Binance Chain",
                curve=secret_data.CurveEnum.SECP256K1,
                chain_affinity="bsc",
                bip44_coin_type=60,
                bip44_target_level=bip44.BIP44Level.ADDRESS_INDEX,
                bip44_auto_increment_level=bip44.BIP44Level.ADDRESS_INDEX,
                bip44_last_hardened_level=bip44.BIP44Level.ACCOUNT,
            ),
        ]
        coins = [
            coin_data.CoinInfo(
                chain_code="btc", name="Bitcoin", code="btc", symbol="BTC", decimals=8, icon=None, token_address=None
            ),
            coin_data.CoinInfo(
                chain_code="eth", name="Ethereum", code="eth", symbol="ETH", decimals=18, icon=None, token_address=None
            ),
            coin_data.CoinInfo(
                chain_code="eth", name="USDT", code="eth_usdt", symbol="USDT", decimals=6, icon=None, token_address=None
            ),
        ]

        patch_loader = patch(
            "common.coin.manager.loader",
            CHAINS_DICT={i.chain_code: i for i in chains},
            COINS_DICT={i.code: i for i in coins},
        )
        patch_loader.start()
        self.addCleanup(patch_loader.stop)

    def test_import_watchonly_wallet_by_address__eth(self):
        wallet_info = wallet_manager.import_watchonly_wallet_by_address(
            "ETH_WATCHONLY", "eth", "0x8Be73940864fD2B15001536E76b3ECcd85a80a5d"
        )
        self.assertEqual(
            {
                "address": "0x8be73940864fd2b15001536e76b3eccd85a80a5d",
                "address_encoding": None,
                "assets": [
                    {
                        "balance": 0,
                        "coin_code": "eth",
                        "decimals": 18,
                        "icon": None,
                        "is_visible": True,
                        "symbol": "ETH",
                        "token_address": None,
                    }
                ],
                "bip44_path": None,
                "chain_code": "eth",
                "name": "ETH_WATCHONLY",
                "wallet_id": 1,
                "wallet_type": "WATCHONLY",
            },
            wallet_info,
        )

    def test_import_watchonly_wallet_by_address__btc(self):
        self.assertEqual(
            {
                "address": "3Nu7tDXHbqtuMfMi3DMVrnLFabTvaY2FyF",
                "address_encoding": "P2WPKH-P2SH",
                "assets": [
                    {
                        "balance": 0,
                        "coin_code": "btc",
                        "decimals": 8,
                        "icon": None,
                        "is_visible": True,
                        "symbol": "BTC",
                        "token_address": None,
                    }
                ],
                "bip44_path": None,
                "chain_code": "btc",
                "name": "BTC_WATCHONLY",
                "wallet_id": 1,
                "wallet_type": "WATCHONLY",
            },
            wallet_manager.import_watchonly_wallet_by_address(
                "BTC_WATCHONLY", "btc", "3Nu7tDXHbqtuMfMi3DMVrnLFabTvaY2FyF"
            ),
        )

    def test_import_watchonly_wallet_by_pubkey(self):
        self.assertEqual(
            {
                "address": "0x8be73940864fd2b15001536e76b3eccd85a80a5d",
                "address_encoding": None,
                "assets": [
                    {
                        "balance": 0,
                        "coin_code": "eth",
                        "decimals": 18,
                        "icon": None,
                        "is_visible": True,
                        "symbol": "ETH",
                        "token_address": None,
                    }
                ],
                "bip44_path": None,
                "chain_code": "eth",
                "name": "ETH_WATCHONLY_BY_PUBKEY",
                "wallet_id": 1,
                "wallet_type": "WATCHONLY",
            },
            wallet_manager.import_watchonly_wallet_by_pubkey(
                "ETH_WATCHONLY_BY_PUBKEY",
                "eth",
                bytes.fromhex("02deb60902c06bfed8d78e33337be995d0b3efc28fbc61b6f88cb5cfb27dc4efd1"),
            ),
        )

    def test_import_standalone_wallet_by_prvkey(self):
        self.assertEqual(
            {
                "address": "0x8be73940864fd2b15001536e76b3eccd85a80a5d",
                "address_encoding": None,
                "assets": [
                    {
                        "balance": 0,
                        "coin_code": "eth",
                        "decimals": 18,
                        "icon": None,
                        "is_visible": True,
                        "symbol": "ETH",
                        "token_address": None,
                    }
                ],
                "bip44_path": None,
                "chain_code": "eth",
                "name": "ETH_BY_PRVKEY",
                "wallet_id": 1,
                "wallet_type": "SOFTWARE_STANDALONE_PRVKEY",
            },
            wallet_manager.import_standalone_wallet_by_prvkey(
                "ETH_BY_PRVKEY",
                "eth",
                bytes.fromhex("77f22e0d920c7b59df81a629dc75c27513b5360a45d55f3253454f5d3cb23bab"),
                "moon",
            ),
        )

    def test_import_standalone_wallet_by_mnemonic(self):
        self.assertEqual(
            {
                "address": "0x8be73940864fd2b15001536e76b3eccd85a80a5d",
                "address_encoding": None,
                "assets": [
                    {
                        "balance": 0,
                        "coin_code": "eth",
                        "decimals": 18,
                        "icon": None,
                        "is_visible": True,
                        "symbol": "ETH",
                        "token_address": None,
                    }
                ],
                "bip44_path": "m/44'/60'/0'/0/0",
                "chain_code": "eth",
                "name": "ETH_BY_MNEMONIC",
                "wallet_id": 1,
                "wallet_type": "SOFTWARE_STANDALONE_MNEMONIC",
            },
            wallet_manager.import_standalone_wallet_by_mnemonic(
                "ETH_BY_MNEMONIC",
                "eth",
                self.mnemonic,
                passphrase=self.passphrase,
                password=self.password,
                bip44_path="m/44'/60'/0'/0/0",
            ),
        )

    def test_create_primary_wallets(self):
        self.assertEqual(
            [
                {
                    "address": "3Nu7tDXHbqtuMfMi3DMVrnLFabTvaY2FyF",
                    "address_encoding": "P2WPKH-P2SH",
                    "assets": [
                        {
                            "balance": 0,
                            "coin_code": "btc",
                            "decimals": 8,
                            "icon": None,
                            "is_visible": True,
                            "symbol": "BTC",
                            "token_address": None,
                        }
                    ],
                    "bip44_path": "m/49'/0'/0'/0/0",
                    "chain_code": "btc",
                    "name": "BTC-1",
                    "wallet_id": 1,
                    "wallet_type": "SOFTWARE_PRIMARY",
                },
                {
                    "address": "0x8be73940864fd2b15001536e76b3eccd85a80a5d",
                    "address_encoding": None,
                    "assets": [
                        {
                            "balance": 0,
                            "coin_code": "eth",
                            "decimals": 18,
                            "icon": None,
                            "is_visible": True,
                            "symbol": "ETH",
                            "token_address": None,
                        }
                    ],
                    "bip44_path": "m/44'/60'/0'/0/0",
                    "chain_code": "eth",
                    "name": "ETH-1",
                    "wallet_id": 2,
                    "wallet_type": "SOFTWARE_PRIMARY",
                },
            ],
            wallet_manager.create_primary_wallets(
                ["btc", "eth"],
                password=self.password,
                mnemonic=self.mnemonic,
                passphrase=self.passphrase,
            ),
        )

    def test_generate_next_bip44_path_for_derived_primary_wallet(self):
        wallet_manager.create_primary_wallets(
            ["btc", "eth"],
            password=self.password,
            mnemonic=self.mnemonic,
            passphrase=self.passphrase,
        )

        self.assertEqual(
            "m/49'/0'/1'/0/0",
            wallet_manager.generate_next_bip44_path_for_derived_primary_wallet("btc", "P2WPKH-P2SH").to_bip44_path(),
        )
        self.assertEqual(
            "m/44'/0'/0'/0/0",
            wallet_manager.generate_next_bip44_path_for_derived_primary_wallet("btc", "P2PKH").to_bip44_path(),
        )
        self.assertEqual(
            "m/84'/0'/0'/0/0",
            wallet_manager.generate_next_bip44_path_for_derived_primary_wallet("btc", "P2WPKH").to_bip44_path(),
        )
        self.assertEqual(
            "m/44'/60'/0'/0/1",
            wallet_manager.generate_next_bip44_path_for_derived_primary_wallet("eth").to_bip44_path(),
        )
        self.assertEqual(
            "m/44'/60'/0'/0/0",
            wallet_manager.generate_next_bip44_path_for_derived_primary_wallet("bsc").to_bip44_path(),
        )

    def test_create_next_derived_primary_wallet(self):
        wallet_manager.create_primary_wallets(
            ["eth"],
            password=self.password,
            mnemonic=self.mnemonic,
            passphrase=self.passphrase,
        )

        self.assertEqual(
            {
                "address": "3Nu7tDXHbqtuMfMi3DMVrnLFabTvaY2FyF",
                "address_encoding": "P2WPKH-P2SH",
                "assets": [
                    {
                        "balance": 0,
                        "coin_code": "btc",
                        "decimals": 8,
                        "icon": None,
                        "is_visible": True,
                        "symbol": "BTC",
                        "token_address": None,
                    }
                ],
                "bip44_path": "m/49'/0'/0'/0/0",
                "chain_code": "btc",
                "name": "BTC-1",
                "wallet_id": 2,
                "wallet_type": "SOFTWARE_PRIMARY",
            },
            wallet_manager.create_next_derived_primary_wallet("btc", "BTC-1", "moon"),
        )

        self.assertEqual(
            {
                "address": "0xd927952eed3a0a838bbe2db0ba5a15673003903d",
                "address_encoding": None,
                "assets": [
                    {
                        "balance": 0,
                        "coin_code": "eth",
                        "decimals": 18,
                        "icon": None,
                        "is_visible": True,
                        "symbol": "ETH",
                        "token_address": None,
                    }
                ],
                "bip44_path": "m/44'/60'/0'/0/1",
                "chain_code": "eth",
                "name": "ETH-2",
                "wallet_id": 3,
                "wallet_type": "SOFTWARE_PRIMARY",
            },
            wallet_manager.create_next_derived_primary_wallet("eth", "ETH-2", "moon"),
        )

        self.assertEqual(
            {
                "address": "34y7g9uRnjJwvu2zLJVMfrucnbzgyYc4af",
                "address_encoding": "P2WPKH-P2SH",
                "assets": [
                    {
                        "balance": 0,
                        "coin_code": "btc",
                        "decimals": 8,
                        "icon": None,
                        "is_visible": True,
                        "symbol": "BTC",
                        "token_address": None,
                    }
                ],
                "bip44_path": "m/49'/0'/1'/0/0",
                "chain_code": "btc",
                "name": "BTC-2",
                "wallet_id": 4,
                "wallet_type": "SOFTWARE_PRIMARY",
            },
            wallet_manager.create_next_derived_primary_wallet("btc", "BTC-2", "moon"),
        )

    def test_export_mnemonic__primary_wallet(self):
        wallet_info = wallet_manager.create_primary_wallets(
            ["eth"],
            password=self.password,
            mnemonic=self.mnemonic,
            passphrase=self.passphrase,
        )[0]
        self.assertEqual(
            (self.mnemonic, self.passphrase),
            wallet_manager.export_mnemonic(wallet_info["wallet_id"], self.password),
        )

    def test_export_mnemonic__standalone_mnemonic_wallet(self):
        wallet_info = wallet_manager.import_standalone_wallet_by_mnemonic(
            "ETH-1",
            "eth",
            password=self.password,
            mnemonic=self.mnemonic,
            passphrase=self.passphrase,
        )

        self.assertEqual(
            (self.mnemonic, self.passphrase), wallet_manager.export_mnemonic(wallet_info["wallet_id"], self.password)
        )

    @patch("common.wallet.manager.provider_manager.get_address")
    def test_search_existing_wallets(self, fake_get_address):
        fake_get_address.side_effect = (
            lambda chain_code, address: provider_data.Address(address=address, balance=18888, existing=True)
            if address == "0xa0331fcfa308e488833de1fe16370b529fa7c720"
            else provider_data.Address(address=address, balance=0, existing=False)
        )

        self.assertEqual(
            [
                {
                    "address": "3Nu7tDXHbqtuMfMi3DMVrnLFabTvaY2FyF",
                    "address_encoding": "P2WPKH-P2SH",
                    "balance": 0,
                    "bip44_path": "m/49'/0'/0'/0/0",
                    "chain_code": "btc",
                    "name": "BTC-1",
                },
                {
                    "address": "0xa0331fcfa308e488833de1fe16370b529fa7c720",
                    "address_encoding": None,
                    "balance": 18888,
                    "bip44_path": "m/44'/60'/0'/0/11",
                    "chain_code": "eth",
                    "name": "ETH-1",
                },
            ],
            wallet_manager.search_existing_wallets(["btc", "eth"], self.mnemonic, passphrase=self.passphrase),
        )

    def test_update_wallet_password(self):
        wallet_info = wallet_manager.import_standalone_wallet_by_mnemonic(
            "ETH-1",
            "eth",
            password=self.password,
            mnemonic=self.mnemonic,
            passphrase=self.passphrase,
        )

        with self.assertRaises(cipher.InvalidPassword):
            wallet_manager.update_wallet_password(wallet_info["wallet_id"], "hello world", "bye")

        wallet_manager.update_wallet_password(wallet_info["wallet_id"], self.password, "bye")
        wallet_manager.update_wallet_password(wallet_info["wallet_id"], "bye", self.password)

    @patch("common.wallet.manager.get_handler_by_chain_model")
    @patch("common.wallet.manager.provider_manager")
    @patch("common.wallet.manager._verify_unsigned_tx")
    def test_pre_send(self, fake_verify_unsigned_tx, fake_provider_manager, fake_get_handler_by_chain_model):
        wallet = wallet_daos.wallet.create_wallet("testing", wallet_data.WalletType.SOFTWARE_PRIMARY, "eth")

        fake_handler = Mock()
        fake_get_handler_by_chain_model.return_value = fake_handler

        fake_verify_unsigned_tx.return_value = (False, "validate failed")

        with self.subTest("First time"):
            fake_unsigned_tx = provider_data.UnsignedTx(fee_limit=1001, fee_price_per_unit=11)
            fake_handler.generate_unsigned_tx.return_value = fake_unsigned_tx
            self.assertEqual(
                {
                    "unsigned_tx": fake_unsigned_tx.to_dict(),
                    "is_valid": False,
                    "validation_message": "validate failed",
                },
                wallet_manager.pre_send(wallet.id, "eth_usdt"),
            )
            fake_provider_manager.verify_address.assert_not_called()
            fake_get_handler_by_chain_model.assert_called_once_with(coin_data.ChainModel.ACCOUNT)
            fake_handler.generate_unsigned_tx.assert_called_once_with(
                wallet.id, "eth_usdt", None, None, None, None, None, None
            )
            fake_verify_unsigned_tx.assert_called_once_with(wallet.id, "eth_usdt", fake_unsigned_tx)
            fake_handler.generate_unsigned_tx.reset_mock()

        with self.subTest("Call with to_address"):
            fake_provider_manager.verify_address.return_value = provider_data.AddressValidation(
                normalized_address="fake_normal_address", display_address="fake_display_address", is_valid=True
            )
            wallet_manager.pre_send(wallet.id, "eth_usdt", "fake_display_address")
            fake_provider_manager.verify_address.assert_called_once_with("eth", "fake_display_address")
            fake_handler.generate_unsigned_tx.assert_called_once_with(
                wallet.id, "eth_usdt", "fake_normal_address", None, None, None, None, None
            )

        with self.subTest("Call with illegal to_address"):
            fake_provider_manager.verify_address.return_value = provider_data.AddressValidation(
                normalized_address="fake_normal_address", display_address="fake_display_address", is_valid=False
            )
            with self.assertRaisesRegex(
                wallet_exceptions.IllegalWalletOperation, "Invalid to_address: 'fake_display_address'"
            ):
                wallet_manager.pre_send(wallet.id, "eth_usdt", "fake_display_address")

    @patch("common.wallet.manager.get_handler_by_chain_model")
    @patch("common.wallet.manager.provider_manager")
    @patch("common.wallet.manager.secret_manager")
    @patch("common.wallet.manager.transaction_manager")
    def test_send__software(
        self,
        fake_transaction_manager,
        fake_secret_manager,
        fake_provider_manager,
        fake_get_handler_by_chain_model,
    ):
        with self.subTest("Illegal wallet type"):
            wallet = wallet_daos.wallet.create_wallet("testing", wallet_data.WalletType.WATCHONLY, "eth")
            with self.assertRaisesRegex(
                wallet_exceptions.IllegalWalletOperation, "Watchonly wallet can not send asset"
            ):
                wallet_manager.send(wallet.id, "eth_usdt", "fake_display_address", 10, "123")

        wallet = wallet_daos.wallet.create_wallet("testing", wallet_data.WalletType.SOFTWARE_PRIMARY, "eth")
        account = wallet_daos.account.create_account(wallet.id, "eth", "my_address", pubkey_id=111)
        wallet_daos.asset.create_asset(wallet.id, account.id, "eth", "eth_usdt")

        with self.subTest("Require password"):
            with self.assertRaisesRegex(wallet_exceptions.IllegalWalletOperation, "Require password"):
                wallet_manager.send(wallet.id, "eth_usdt", "fake_display_address", 10)

        with self.subTest("Send asset"):
            fake_handler = Mock()
            fake_unsigned_tx = provider_data.UnsignedTx(
                inputs=[provider_data.TransactionInput(address="my_address", value=10)],
                outputs=[provider_data.TransactionOutput(address="fake_normal_address", value=10)],
                nonce=3,
                fee_limit=101,
                fee_price_per_unit=11,
            )
            fake_handler.generate_unsigned_tx.return_value = fake_unsigned_tx
            fake_get_handler_by_chain_model.return_value = fake_handler

            fake_provider_manager.verify_address.return_value = provider_data.AddressValidation(
                normalized_address="fake_normal_address", display_address="fake_display_address", is_valid=True
            )
            fake_provider_manager.sign_transaction.return_value = provider_data.SignedTx(
                txid="fake_txid", raw_tx="fake_raw_tx"
            )
            fake_provider_manager.broadcast_transaction.return_value = provider_data.TxBroadcastReceipt(
                txid="fake_txid", is_success=True, receipt_code=provider_data.TxBroadcastReceiptCode.SUCCESS
            )

            fake_signer = Mock()
            fake_secret_manager.get_signer.return_value = fake_signer

            self.assertEqual(
                provider_data.SignedTx(txid="fake_txid", raw_tx="fake_raw_tx"),
                wallet_manager.send(wallet.id, "eth_usdt", "fake_display_address", 10, "123"),
            )

            fake_get_handler_by_chain_model.assert_called_once_with(coin_data.ChainModel.ACCOUNT)
            fake_provider_manager.verify_address.assert_has_calls(
                [call("eth", "fake_display_address"), call("eth", "fake_normal_address")]
            )
            fake_handler.generate_unsigned_tx.assert_called_once_with(
                wallet.id, "eth_usdt", "fake_normal_address", 10, None, None, None, None
            )
            fake_secret_manager.get_signer.assert_called_once_with("123", 111)
            fake_provider_manager.sign_transaction.assert_called_once_with(
                "eth", fake_unsigned_tx, {"my_address": fake_signer}
            )
            fake_provider_manager.broadcast_transaction.assert_called_once_with("eth", "fake_raw_tx")
            fake_transaction_manager.update_action_status.assert_called_once_with(
                "eth", "fake_txid", transaction_data.TxActionStatus.PENDING
            )
            fake_transaction_manager.create_action.assert_called_once_with(
                txid="fake_txid",
                status=transaction_data.TxActionStatus.PENDING,
                chain_code="eth",
                coin_code="eth_usdt",
                value=decimal.Decimal(10),
                from_address="my_address",
                to_address="fake_normal_address",
                fee_limit=decimal.Decimal(101),
                fee_price_per_unit=decimal.Decimal(11),
                nonce=3,
                raw_tx="fake_raw_tx",
            )

    @patch("common.wallet.manager.provider_manager")
    @patch("common.wallet.manager.transaction_manager")
    def test_broadcast_transaction(self, fake_transaction_manager, fake_provider_manager):
        with self.subTest("broadcast success"):
            fake_receipt = provider_data.TxBroadcastReceipt(
                is_success=True, txid="fake_txid", receipt_code=provider_data.TxBroadcastReceiptCode.SUCCESS
            )
            fake_provider_manager.broadcast_transaction.return_value = fake_receipt
            self.assertEqual(
                fake_receipt,
                wallet_manager.broadcast_transaction(
                    "eth", provider_data.SignedTx(txid="fake_txid", raw_tx="fake_raw_tx")
                ),
            )

            fake_provider_manager.broadcast_transaction.assert_called_once_with("eth", "fake_raw_tx")
            fake_transaction_manager.update_action_status.assert_called_once_with(
                "eth", "fake_txid", transaction_data.TxActionStatus.PENDING
            )
            fake_provider_manager.broadcast_transaction.reset_mock()
            fake_transaction_manager.update_action_status.reset_mock()

        with self.subTest("broadcast failed"):
            fake_receipt = provider_data.TxBroadcastReceipt(
                is_success=False, txid="fake_txid", receipt_code=provider_data.TxBroadcastReceiptCode.UNEXPECTED_FAILED
            )
            fake_provider_manager.broadcast_transaction.return_value = fake_receipt
            self.assertEqual(
                fake_receipt,
                wallet_manager.broadcast_transaction(
                    "eth", provider_data.SignedTx(txid="fake_txid", raw_tx="fake_raw_tx")
                ),
            )
            fake_provider_manager.broadcast_transaction.assert_called_once_with("eth", "fake_raw_tx")
            fake_transaction_manager.update_action_status.assert_called_once_with(
                "eth", "fake_txid", transaction_data.TxActionStatus.UNEXPECTED_FAILED
            )
            fake_provider_manager.broadcast_transaction.reset_mock()
            fake_transaction_manager.update_action_status.reset_mock()

        with self.subTest("Txid mismatched"):
            fake_receipt = provider_data.TxBroadcastReceipt(
                is_success=False, txid="fake_txid2", receipt_code=provider_data.TxBroadcastReceiptCode.UNEXPECTED_FAILED
            )
            fake_provider_manager.broadcast_transaction.return_value = fake_receipt
            with self.assertRaisesRegex(AssertionError, "Txid mismatched. expected: fake_txid, actual: fake_txid2"):
                wallet_manager.broadcast_transaction(
                    "eth", provider_data.SignedTx(txid="fake_txid", raw_tx="fake_raw_tx")
                )

        with self.subTest("Txid filling"):
            fake_receipt = provider_data.TxBroadcastReceipt(
                is_success=True, receipt_code=provider_data.TxBroadcastReceiptCode.SUCCESS
            )
            fake_provider_manager.broadcast_transaction.return_value = fake_receipt
            self.assertEqual(
                fake_receipt.clone(txid="fake_txid"),
                wallet_manager.broadcast_transaction(
                    "eth", provider_data.SignedTx(txid="fake_txid", raw_tx="fake_raw_tx")
                ),
            )

    @patch("common.wallet.manager.get_default_account_by_wallet")
    def test_create_or_show_asset(self, fake_get_default_account_by_wallet):
        with self.subTest("Create asset as expected"):
            fake_get_default_account_by_wallet.return_value = Mock(id=1001, chain_code="eth")

            wallet_manager.create_or_show_asset(11, "eth_usdt")

            assets = wallet_daos.asset.query_assets_by_accounts([1001])
            self.assertEqual(1, len(assets))
            testing_asset = assets[0]
            self.assertEqual(
                (11, 1001, "eth", "eth_usdt", True),
                (
                    testing_asset.wallet_id,
                    testing_asset.account_id,
                    testing_asset.chain_code,
                    testing_asset.coin_code,
                    testing_asset.is_visible,
                ),
            )
            fake_get_default_account_by_wallet.assert_called_once_with(11)

        wallet_daos.asset.hide_asset(testing_asset.id)
        testing_asset = wallet_daos.asset.query_assets_by_ids([testing_asset.id])[0]
        self.assertFalse(testing_asset.is_visible)

        with self.subTest("Show created asset again"):
            wallet_manager.create_or_show_asset(11, "eth_usdt")
            testing_asset = wallet_daos.asset.query_assets_by_ids([testing_asset.id])[0]
            self.assertTrue(testing_asset.is_visible)

    @patch("common.wallet.manager.get_default_account_by_wallet")
    def test_hide_asset(self, fake_get_default_account_by_wallet):
        with self.subTest("Asset not found"):
            fake_get_default_account_by_wallet.return_value = Mock(id=1001, chain_code="eth")

            with self.assertRaisesRegex(
                wallet_exceptions.IllegalWalletOperation, "Asset not found. wallet_id: 11, coin_code: eth_usdt"
            ):
                wallet_manager.hide_asset(11, "eth_usdt")

        with self.subTest("Hide asset as expected"):
            asset = wallet_daos.asset.create_asset(11, 1001, "eth", "eth_usdt")
            self.assertTrue(asset.is_visible)
            wallet_manager.hide_asset(11, "eth_usdt")
            asset = wallet_daos.asset.query_assets_by_ids([asset.id])[0]
            self.assertFalse(asset.is_visible)

    @patch("common.wallet.manager.coin_manager")
    @patch("common.wallet.manager.provider_manager")
    def test_refresh_assets(self, fake_provider_manager, fake_coin_manager):
        account = wallet_daos.account.create_account(11, "eth", "fake_address")
        asset_a = wallet_daos.asset.create_asset(11, account.id, "eth", "eth_usdt")
        asset_b = wallet_daos.asset.create_asset(11, account.id, "eth", "eth_cc")

        fake_coin_manager.query_coins_by_codes.return_value = [
            Mock(code="eth_usdt", token_address="contract_a"),
            Mock(code="eth_cc", token_address="contract_b"),
        ]
        fake_provider_manager.get_balance.side_effect = lambda chain_code, address, token_address: {
            "contract_a": 11,
            "contract_b": 12,
        }.get(token_address)

        with self.subTest("Refresh nothing"):
            self.assertEqual([asset_a, asset_b], wallet_manager.refresh_assets([asset_a, asset_b]))
            fake_coin_manager.query_coins_by_codes.assert_not_called()
            fake_provider_manager.get_balance.assert_not_called()

        with self.subTest("Refresh asset_b"):
            wallet_models.AssetModel.update(
                modified_time=datetime.datetime.now() - datetime.timedelta(seconds=10)
            ).where(wallet_models.AssetModel.id == asset_b.id).execute()
            asset_b = wallet_models.AssetModel.get_by_id(asset_b.id)

            asset_a, asset_b = wallet_manager.refresh_assets([asset_a, asset_b])
            self.assertEqual(12, asset_b.balance)
            fake_coin_manager.query_coins_by_codes.assert_called_once_with(["eth_cc"])
            fake_provider_manager.get_balance.assert_called_once_with("eth", "fake_address", "contract_b")
            fake_coin_manager.query_coins_by_codes.reset_mock()
            fake_provider_manager.get_balance.reset_mock()

        with self.subTest("Refresh all"):
            asset_a, asset_b = wallet_manager.refresh_assets([asset_a, asset_b], force_update=True)
            self.assertEqual(11, asset_a.balance)
            self.assertEqual(12, asset_b.balance)
            fake_coin_manager.query_coins_by_codes.assert_called_once_with(["eth_usdt", "eth_cc"])
            fake_provider_manager.get_balance.assert_has_calls(
                [
                    call("eth", "fake_address", "contract_a"),
                    call("eth", "fake_address", "contract_b"),
                ]
            )

    def test_get_default_bip44_path(self):
        self.assertEqual("m/44'/0'/0'/0/0", wallet_manager.get_default_bip44_path("btc", "P2PKH").to_bip44_path())
        self.assertEqual("m/49'/0'/0'/0/0", wallet_manager.get_default_bip44_path("btc", "P2WPKH-P2SH").to_bip44_path())
        self.assertEqual("m/84'/0'/0'/0/0", wallet_manager.get_default_bip44_path("btc", "P2WPKH").to_bip44_path())
        self.assertEqual("m/44'/60'/0'/0/0", wallet_manager.get_default_bip44_path("eth").to_bip44_path())

    def test_cascade_delete_wallet_related_models(self):
        wallet_info = wallet_manager.import_standalone_wallet_by_mnemonic(
            "ETH_BY_MNEMONIC",
            "eth",
            self.mnemonic,
            passphrase=self.passphrase,
            password=self.password,
            bip44_path="m/44'/60'/0'/0/0",
        )
        transaction_manager.create_action(
            txid="fake_id",
            status=transaction_data.TxActionStatus.CONFIRM_SUCCESS,
            chain_code="eth",
            coin_code="eth",
            value=decimal.Decimal(1),
            from_address=wallet_info["address"],
            to_address="0x0001",
            fee_limit=decimal.Decimal(1),
            fee_price_per_unit=decimal.Decimal(1),
            nonce=0,
            raw_tx="",
        )

        self.assertEqual(1, secret_models.SecretKeyModel.select().count())
        self.assertEqual(1, secret_models.PubKeyModel.select().count())
        self.assertEqual(1, wallet_models.WalletModel.select().count())
        self.assertEqual(1, wallet_models.AccountModel.select().count())
        self.assertEqual(1, wallet_models.AssetModel.select().count())
        self.assertEqual(1, transaction_models.TxAction.select().count())

        wallet_manager.cascade_delete_wallet_related_models(wallet_info["wallet_id"], self.password)

        self.assertEqual(0, secret_models.SecretKeyModel.select().count())
        self.assertEqual(0, secret_models.PubKeyModel.select().count())
        self.assertEqual(0, wallet_models.WalletModel.select().count())
        self.assertEqual(0, wallet_models.AccountModel.select().count())
        self.assertEqual(0, wallet_models.AssetModel.select().count())
        self.assertEqual(0, transaction_models.TxAction.select().count())

    @patch("common.wallet.manager.get_handler_by_chain_model")
    @patch("common.wallet.manager.provider_manager")
    @patch("common.wallet.manager.transaction_manager")
    @patch("common.wallet.manager.hardware_manager")
    def test_send__hardware(
        self,
        fake_hardware_manager,
        fake_transaction_manager,
        fake_provider_manager,
        fake_get_handler_by_chain_model,
    ):
        hardware_key_id = "fake_hardware_key_id"
        hardware_device_path = "fake_device_path"

        wallet = wallet_daos.wallet.create_wallet(
            "testing",
            wallet_data.WalletType.HARDWARE_PRIMARY,
            "eth",
            hardware_key_id=hardware_key_id,
        )
        account = wallet_daos.account.create_account(wallet.id, "eth", "my_address", bip44_path="m/44'/60'/0'/0/1024")
        wallet_daos.asset.create_asset(wallet.id, account.id, "eth", "eth_usdt")

        with self.subTest("Require hardware_key_id"):
            with self.assertRaisesRegex(wallet_exceptions.IllegalWalletOperation, "Require hardware_device_path"):
                wallet_manager.send(wallet.id, "eth_usdt", "fake_display_address", 10)

        with self.subTest("Device mismatch"):
            fake_hardware_manager.get_key_id.return_value = "other_hardware_key_id"
            with self.assertRaisesRegex(wallet_exceptions.IllegalWalletOperation, "Device mismatch"):
                wallet_manager.send(
                    wallet.id, "eth_usdt", "fake_display_address", 10, hardware_device_path=hardware_device_path
                )

            fake_hardware_manager.get_key_id.assert_called_once_with(hardware_device_path)
            fake_hardware_manager.get_key_id.reset_mock()

        with self.subTest("Send asset"):
            fake_hardware_manager.get_key_id.return_value = hardware_key_id

            fake_handler = Mock()
            fake_unsigned_tx = provider_data.UnsignedTx(
                inputs=[provider_data.TransactionInput(address="my_address", value=10)],
                outputs=[provider_data.TransactionOutput(address="fake_normal_address", value=10)],
                nonce=3,
                fee_limit=101,
                fee_price_per_unit=11,
            )
            fake_handler.generate_unsigned_tx.return_value = fake_unsigned_tx
            fake_get_handler_by_chain_model.return_value = fake_handler

            fake_provider_manager.verify_address.return_value = provider_data.AddressValidation(
                normalized_address="fake_normal_address", display_address="fake_display_address", is_valid=True
            )
            fake_provider_manager.hardware_sign_transaction.return_value = provider_data.SignedTx(
                txid="fake_txid", raw_tx="fake_raw_tx"
            )
            fake_provider_manager.broadcast_transaction.return_value = provider_data.TxBroadcastReceipt(
                txid="fake_txid", is_success=True, receipt_code=provider_data.TxBroadcastReceiptCode.SUCCESS
            )

            self.assertEqual(
                provider_data.SignedTx(txid="fake_txid", raw_tx="fake_raw_tx"),
                wallet_manager.send(
                    wallet.id, "eth_usdt", "fake_display_address", 10, hardware_device_path=hardware_device_path
                ),
            )

            fake_get_handler_by_chain_model.assert_called_once_with(coin_data.ChainModel.ACCOUNT)
            fake_provider_manager.verify_address.assert_has_calls(
                [call("eth", "fake_display_address"), call("eth", "fake_normal_address")]
            )
            fake_handler.generate_unsigned_tx.assert_called_once_with(
                wallet.id, "eth_usdt", "fake_normal_address", 10, None, None, None, None
            )
            fake_provider_manager.hardware_sign_transaction.assert_called_once_with(
                "eth",
                hardware_device_path,
                fake_unsigned_tx,
                {"my_address": "m/44'/60'/0'/0/1024"},
            )
            fake_provider_manager.broadcast_transaction.assert_called_once_with("eth", "fake_raw_tx")
            fake_transaction_manager.update_action_status.assert_called_once_with(
                "eth", "fake_txid", transaction_data.TxActionStatus.PENDING
            )
            fake_transaction_manager.create_action.assert_called_once_with(
                txid="fake_txid",
                status=transaction_data.TxActionStatus.PENDING,
                chain_code="eth",
                coin_code="eth_usdt",
                value=decimal.Decimal(10),
                from_address="my_address",
                to_address="fake_normal_address",
                fee_limit=decimal.Decimal(101),
                fee_price_per_unit=decimal.Decimal(11),
                nonce=3,
                raw_tx="fake_raw_tx",
            )

    @patch("common.wallet.manager.hardware_manager")
    def test_generate_next_bip44_path_for_primary_hardware_wallet(self, fake_hardware_manager):
        hardware_device_path = "fake_hardware_device_path"
        hardware_key_id = "fake_hardware_key_id"
        fake_hardware_manager.get_key_id.return_value = hardware_key_id

        with self.subTest("no hardware wallet yet"):
            self.assertEqual(
                "m/44'/60'/0'/0/0",
                wallet_manager.generate_next_bip44_path_for_primary_hardware_wallet(
                    "eth", hardware_device_path
                ).to_bip44_path(),
            )
            fake_hardware_manager.get_key_id.assert_called_once_with(hardware_device_path)

        with self.subTest("auto increase next bip44 path"):
            wallet = wallet_daos.wallet.create_wallet(
                "testing",
                wallet_data.WalletType.HARDWARE_PRIMARY,
                "eth",
                hardware_key_id=hardware_key_id,
            )
            wallet_daos.account.create_account(wallet.id, "eth", "my_address", bip44_path="m/44'/60'/0'/0/0")
            self.assertEqual(
                "m/44'/60'/0'/0/1",
                wallet_manager.generate_next_bip44_path_for_primary_hardware_wallet(
                    "eth", hardware_device_path
                ).to_bip44_path(),
            )

        with self.subTest("different hardware_key_id different branch"):
            fake_hardware_manager.get_key_id.return_value = "other_hardware_key_id"
            self.assertEqual(
                "m/44'/60'/0'/0/0",
                wallet_manager.generate_next_bip44_path_for_primary_hardware_wallet(
                    "eth", hardware_device_path
                ).to_bip44_path(),
            )

    @patch("common.wallet.manager.provider_manager.hardware_get_xpub")
    @patch("common.wallet.manager.hardware_manager")
    def test_create_next_primary_hardware_wallet(self, fake_hardware_manager, fake_hardware_get_xpub):
        hardware_device_path = "fake_hardware_device_path"
        hardware_key_id = "fake_hardware_key_id"
        fake_hardware_manager.get_key_id.return_value = hardware_key_id

        self.assertEqual(0, wallet_models.WalletModel.select().count())
        self.assertEqual(0, secret_models.PubKeyModel.select().count())

        with self.subTest("the first wallet"):
            fake_hardware_get_xpub.return_value = "xpub6GdekQL5Q9Fs4bcPdEs8L8gwz9paLoVQ4gXxAzGX8b4uuC4NpmxZQofSXpWDuFRhHiphExDLEGrxdDP8jPJfz8yBV2dhvzaGfRBvdA6FPFF"
            self.assertEqual(
                {
                    "address": "0x8be73940864fd2b15001536e76b3eccd85a80a5d",
                    "address_encoding": None,
                    "assets": [
                        {
                            "balance": 0,
                            "coin_code": "eth",
                            "decimals": 18,
                            "icon": None,
                            "is_visible": True,
                            "symbol": "ETH",
                            "token_address": None,
                        }
                    ],
                    "bip44_path": "m/44'/60'/0'/0/0",
                    "chain_code": "eth",
                    "name": "hw_1",
                    "wallet_id": 1,
                    "wallet_type": "HARDWARE_PRIMARY",
                },
                wallet_manager.create_next_primary_hardware_wallet("hw_1", "eth", hardware_device_path),
            )
            self.assertEqual(1, wallet_models.WalletModel.select().count())
            self.assertEqual(1, secret_models.PubKeyModel.select().count())
            fake_hardware_manager.get_key_id.assert_called_once_with(hardware_device_path)
            fake_hardware_get_xpub.assert_called_once_with("eth", hardware_device_path, "m/44'/60'/0'/0/0")

        with self.subTest("the second wallet"):
            fake_hardware_get_xpub.return_value = "xpub6GdekQL5Q9Fs6eZYGrYCYy1ewvg1cQV2wDTpMvFCcgFFuKREY1tqsvRYrudxVLdHdJveLEEV4w3bneUoxJsxzURjkMm2nQBUnmZeXyRKwDr"
            self.assertEqual(
                {
                    "address": "0xd927952eed3a0a838bbe2db0ba5a15673003903d",
                    "address_encoding": None,
                    "assets": [
                        {
                            "balance": 0,
                            "coin_code": "eth",
                            "decimals": 18,
                            "icon": None,
                            "is_visible": True,
                            "symbol": "ETH",
                            "token_address": None,
                        }
                    ],
                    "bip44_path": "m/44'/60'/0'/0/1",
                    "chain_code": "eth",
                    "name": "hw_2",
                    "wallet_id": 2,
                    "wallet_type": "HARDWARE_PRIMARY",
                },
                wallet_manager.create_next_primary_hardware_wallet("hw_2", "eth", hardware_device_path),
            )
            self.assertEqual(2, wallet_models.WalletModel.select().count())
            self.assertEqual(2, secret_models.PubKeyModel.select().count())

    @patch("common.wallet.manager.provider_manager.hardware_get_xpub")
    @patch("common.wallet.manager.hardware_manager")
    def test_create_standalone_hardware_wallet(self, fake_hardware_manager, fake_hardware_get_xpub):
        hardware_device_path = "fake_hardware_device_path"
        hardware_key_id = "fake_hardware_key_id"
        fake_hardware_manager.get_key_id.return_value = hardware_key_id

        fake_hardware_get_xpub.return_value = "xpub6GdekQL5Q9Fs6eZYGrYCYy1ewvg1cQV2wDTpMvFCcgFFuKREY1tqsvRYrudxVLdHdJveLEEV4w3bneUoxJsxzURjkMm2nQBUnmZeXyRKwDr"
        self.assertEqual(
            {
                "address": "0xd927952eed3a0a838bbe2db0ba5a15673003903d",
                "address_encoding": None,
                "assets": [
                    {
                        "balance": 0,
                        "coin_code": "eth",
                        "decimals": 18,
                        "icon": None,
                        "is_visible": True,
                        "symbol": "ETH",
                        "token_address": None,
                    }
                ],
                "bip44_path": "m/44'/60'/0'/0/1",
                "chain_code": "eth",
                "name": "hw_1",
                "wallet_id": 1,
                "wallet_type": "HARDWARE_STANDALONE",
            },
            wallet_manager.create_standalone_hardware_wallet("hw_1", "eth", hardware_device_path, "m/44'/60'/0'/0/1"),
        )
        fake_hardware_get_xpub.assert_called_once_with("eth", hardware_device_path, "m/44'/60'/0'/0/1")

    @patch("common.wallet.manager.provider_manager")
    @patch("common.wallet.manager.hardware_manager")
    def test_sign_message__hardware(self, fake_hardware_manager, fake_provider_manager):
        hardware_key_id = "fake_hardware_key_id"
        hardware_device_path = "fake_device_path"

        wallet = wallet_daos.wallet.create_wallet(
            "testing",
            wallet_data.WalletType.HARDWARE_PRIMARY,
            "eth",
            hardware_key_id=hardware_key_id,
        )
        account = wallet_daos.account.create_account(wallet.id, "eth", "my_address", bip44_path="m/44'/60'/0'/0/1024")
        wallet_daos.asset.create_asset(wallet.id, account.id, "eth", "eth_usdt")

        with self.subTest("Require hardware_key_id"):
            with self.assertRaisesRegex(wallet_exceptions.IllegalWalletOperation, "Require hardware_device_path"):
                wallet_manager.sign_message(wallet.id, "Hello OneKey")

        with self.subTest("Device mismatch"):
            fake_hardware_manager.get_key_id.return_value = "other_hardware_key_id"
            with self.assertRaisesRegex(wallet_exceptions.IllegalWalletOperation, "Device mismatch"):
                wallet_manager.sign_message(wallet.id, "Hello OneKey", hardware_device_path=hardware_device_path)

            fake_hardware_manager.get_key_id.assert_called_once_with(hardware_device_path)
            fake_hardware_manager.get_key_id.reset_mock()

        with self.subTest("Sign message"):
            fake_hardware_manager.get_key_id.return_value = hardware_key_id
            fake_provider_manager.hardware_sign_message.return_value = "fake_signature"
            self.assertEqual(
                "fake_signature",
                wallet_manager.sign_message(wallet.id, "Hello OneKey", hardware_device_path=hardware_device_path),
            )
            fake_provider_manager.hardware_sign_message.assert_called_once_with(
                "eth", hardware_device_path, "Hello OneKey", "m/44'/60'/0'/0/1024"
            )

    @patch("common.wallet.manager.provider_manager")
    @patch("common.wallet.manager.secret_manager")
    def test_sign_message__software(self, fake_secret_manager, fake_provider_manager):
        wallet = wallet_daos.wallet.create_wallet("testing", wallet_data.WalletType.SOFTWARE_PRIMARY, "eth")
        account = wallet_daos.account.create_account(wallet.id, "eth", "my_address", pubkey_id=111)
        wallet_daos.asset.create_asset(wallet.id, account.id, "eth", "eth_usdt")

        fake_signer = Mock()
        fake_secret_manager.get_signer.return_value = fake_signer
        fake_provider_manager.sign_message.return_value = "fake_signature"

        self.assertEqual("fake_signature", wallet_manager.sign_message(wallet.id, "Hello OneKey", self.password))
        fake_secret_manager.get_signer.assert_called_once_with(self.password, 111)
        fake_provider_manager.sign_message.assert_called_once_with(
            "eth", "Hello OneKey", fake_signer, address="my_address"
        )

    @patch("common.wallet.manager.provider_manager")
    def test_verify_message__hardware(self, fake_provider_manager):
        fake_provider_manager.hardware_verify_message.return_value = True
        fake_provider_manager.verify_address.return_value = Mock(normalized_address="fake_address")

        self.assertEqual(
            True,
            wallet_manager.verify_message("eth", "fake_address", "Hello OneKey", "fake_signature", "fake_device_path"),
        )
        fake_provider_manager.verify_address.assert_called_once_with("eth", "fake_address")
        fake_provider_manager.hardware_verify_message.assert_called_once_with(
            "eth", "fake_device_path", "fake_address", "Hello OneKey", "fake_signature"
        )

    @patch("common.wallet.manager.provider_manager")
    def test_verify_message__software(self, fake_provider_manager):
        fake_provider_manager.verify_message.return_value = True
        fake_provider_manager.verify_address.return_value = Mock(normalized_address="fake_address")

        self.assertEqual(
            True,
            wallet_manager.verify_message("eth", "fake_address", "Hello OneKey", "fake_signature"),
        )
        fake_provider_manager.verify_address.assert_called_once_with("eth", "fake_address")
        fake_provider_manager.verify_message.assert_called_once_with(
            "eth", "fake_address", "Hello OneKey", "fake_signature"
        )
