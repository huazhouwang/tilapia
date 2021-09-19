from unittest import TestCase
from unittest.mock import Mock

from wallet.lib.provider import data
from wallet.lib.provider.chains.btc import provider
from wallet.lib.secret import data as secret_data
from wallet.lib.secret import manager as secret_manager


class TestBTCProvider(TestCase):
    def setUp(self) -> None:
        self.fake_chain_info = Mock(
            chain_code="btc",
            default_address_encoding="P2WPKH-P2SH",
            bip44_purpose_options={"P2PKH": 44, "P2WPKH-P2SH": 49, "P2WPKH": 84},
        )
        self.fake_coins_loader = Mock()
        self.fake_client = Mock()
        self.fake_client_selector = Mock(return_value=self.fake_client)
        self.provider = provider.BTCProvider(
            chain_info=self.fake_chain_info,
            coins_loader=self.fake_coins_loader,
            client_selector=self.fake_client_selector,
        )
        self.signer = secret_manager.raw_create_key_by_prvkey(
            secret_data.CurveEnum.SECP256K1,
            bytes.fromhex("0000000000000000000000000000000000000000000000000000000000000001"),
        )

    def test_verify_address(self):
        self.assertEqual(
            data.AddressValidation(
                normalized_address="1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH",
                display_address="1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH",
                is_valid=True,
                encoding="P2PKH",
            ),
            self.provider.verify_address("1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH"),
        )
        self.assertEqual(
            data.AddressValidation(
                normalized_address="bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4",
                display_address="bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4",
                is_valid=True,
                encoding="P2WPKH",
            ),
            self.provider.verify_address("bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4"),
        )
        self.assertEqual(
            data.AddressValidation(
                normalized_address="3JvL6Ymt8MVWiCNHC7oWU6nLeHNJKLZGLN",
                display_address="3JvL6Ymt8MVWiCNHC7oWU6nLeHNJKLZGLN",
                is_valid=True,
                encoding="P2WPKH-P2SH",
            ),
            self.provider.verify_address("3JvL6Ymt8MVWiCNHC7oWU6nLeHNJKLZGLN"),
        )
        self.assertEqual(
            data.AddressValidation(
                normalized_address="",
                display_address="",
                is_valid=False,
            ),
            self.provider.verify_address("moEpB3BcDGzcrxif7ViauHrBQm7Nx1gEqB"),  # XTN P2PKH Address
        )

    def test_pubkey_to_address(self):
        verifier = self.signer.as_pubkey_version()
        self.assertEqual("1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH", self.provider.pubkey_to_address(verifier, "P2PKH"))
        self.assertEqual(
            "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4", self.provider.pubkey_to_address(verifier, "P2WPKH")
        )
        self.assertEqual("3JvL6Ymt8MVWiCNHC7oWU6nLeHNJKLZGLN", self.provider.pubkey_to_address(verifier, "P2WPKH-P2SH"))

        with self.assertRaisesRegex(Exception, "Invalid address encoding: P2MOON"):
            self.provider.pubkey_to_address(verifier, "P2MOON")

    def test_fill_unsigned_tx__empty(self):
        with self.subTest("Get normal fee rate if there is no value on fee_price_per_unit"):
            self.fake_client.get_prices_per_unit_of_fee.return_value = Mock(normal=Mock(price=2))
            self.assertEqual(
                data.UnsignedTx(
                    fee_price_per_unit=2,
                    fee_limit=79,
                ),
                self.provider.fill_unsigned_tx(data.UnsignedTx()),
            )
            self.fake_client.get_prices_per_unit_of_fee.assert_called_once()

        with self.subTest("Without call"):
            self.fake_client.get_prices_per_unit_of_fee.reset_mock()
            self.assertEqual(
                data.UnsignedTx(
                    fee_price_per_unit=3,
                    fee_limit=79,
                ),
                self.provider.fill_unsigned_tx(data.UnsignedTx(fee_price_per_unit=3)),
            )
            self.fake_client.get_prices_per_unit_of_fee.assert_not_called()

    def test_fill_unsigned_tx__inputs_outputs(self):
        unsigned_tx = data.UnsignedTx(
            inputs=[
                data.TransactionInput(
                    address="1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH",
                    value=1000,
                    utxo=data.UTXO(
                        txid="42fb4111cbef992dc10095a976efceb09f0f57a4ce0794d8e9cab4ceb3d35c7a", vout=0, value=1000
                    ),
                ),
                data.TransactionInput(
                    address="3JvL6Ymt8MVWiCNHC7oWU6nLeHNJKLZGLN",
                    value=2000,
                    utxo=data.UTXO(
                        txid="42fb4111cbef992dc10095a976efceb09f0f57a4ce0794d8e9cab4ceb3d35c7a", vout=1, value=1000
                    ),
                ),
            ],
            outputs=[
                data.TransactionOutput(address="bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4", value=1500),
                data.TransactionOutput(address="3JvL6Ymt8MVWiCNHC7oWU6nLeHNJKLZGLN", value=1163),
            ],
            fee_price_per_unit=3,
            payload=dict(op_return="Hello OneKey"),
        )
        self.assertEqual(unsigned_tx.clone(fee_limit=337), self.provider.fill_unsigned_tx(unsigned_tx))

    def test_sign_transaction(self):
        unsigned_tx = data.UnsignedTx(
            inputs=[
                data.TransactionInput(
                    address="1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH",
                    value=1000,
                    utxo=data.UTXO(
                        txid="42fb4111cbef992dc10095a976efceb09f0f57a4ce0794d8e9cab4ceb3d35c7a", vout=0, value=1000
                    ),
                ),
                data.TransactionInput(
                    address="3JvL6Ymt8MVWiCNHC7oWU6nLeHNJKLZGLN",
                    value=2000,
                    utxo=data.UTXO(
                        txid="42fb4111cbef992dc10095a976efceb09f0f57a4ce0794d8e9cab4ceb3d35c7a", vout=1, value=1000
                    ),
                ),
            ],
            outputs=[
                data.TransactionOutput(address="bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4", value=1500),
                data.TransactionOutput(address="3JvL6Ymt8MVWiCNHC7oWU6nLeHNJKLZGLN", value=1163),
            ],
            fee_price_per_unit=3,
            fee_limit=337,
            payload=dict(op_return="Hello OneKey"),
        )
        self.assertEqual(
            data.SignedTx(
                raw_tx="010000000001027a5cd3b3ceb4cae9d89407cea4570f9fb0ceef76a99500c12d99efcb1141fb42000000006b4830450221008317f67e8e5030368ee81810f6470385ba0d1602fbc0cde32900927ca3978e2f0220686d824988db30c33a8dbfbe91de707cfac5d2b78131a8fecb1fc56c840724ff01210279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798ffffffff7a5cd3b3ceb4cae9d89407cea4570f9fb0ceef76a99500c12d99efcb1141fb420100000017160014751e76e8199196d454941c45d1b3a323f1433bd6ffffffff03dc05000000000000160014751e76e8199196d454941c45d1b3a323f1433bd68b0400000000000017a914bcfeb728b584253d5f3f70bcb780e9ef218a68f48700000000000000000e6a0c48656c6c6f204f6e654b6579000247304402202a5dfce171db0acff89d2c7210279c4bc13e29132d55864a2365e3ff0042d0f8022004ddee0a5156f5cfb69db3ba5ef17baabfd395261477948eaf518fff10db73c701210279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f8179800000000",
                txid="b7d23466fb080dc165c8f898060c357c375fd29749108bba9c4649b39a4021d1",
            ),
            self.provider.sign_transaction(
                unsigned_tx,
                {"1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH": self.signer, "3JvL6Ymt8MVWiCNHC7oWU6nLeHNJKLZGLN": self.signer},
            ),
        )
