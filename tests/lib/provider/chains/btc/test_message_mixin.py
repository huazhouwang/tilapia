from unittest import TestCase
from unittest.mock import Mock

from wallet.lib.provider.chains.btc import provider
from wallet.lib.secret import data as secret_data
from wallet.lib.secret import manager as secret_manager


class TestBTCMessageMixin(TestCase):
    def setUp(self) -> None:
        self.fake_chain_info = Mock(
            chain_code="btc",
            default_address_encoding="P2WPKH-P2SH",
            bip44_purpose_options={"P2PKH": 44, "P2WPKH-P2SH": 49, "P2WPKH": 84},
        )
        self.fake_coins_loader = Mock()
        self.fake_client_selector = Mock()
        self.provider = provider.BTCProvider(
            chain_info=self.fake_chain_info,
            coins_loader=self.fake_coins_loader,
            client_selector=self.fake_client_selector,
        )

        self.message = "Hello OneKey"

        self.signer = secret_manager.raw_create_key_by_prvkey(
            secret_data.CurveEnum.SECP256K1,
            bytes.fromhex("0000000000000000000000000000000000000000000000000000000000000001"),
        )
        self.p2pkh_address = "1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH"
        self.p2wpkh_address = "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4"
        self.p2wpkh_p2sh_address = "3JvL6Ymt8MVWiCNHC7oWU6nLeHNJKLZGLN"

    def test_sign_message(self):
        self.assertEqual(
            "H8eojIhqVBXWAIRRLwl1wOQyPeAwGlZgbGwcDXH+kNlbFhbJPS4eWW5cDwFgIkgna9u2hZ1TS9iUuVjyCKpNm9c=",
            self.provider.sign_message(self.message, self.signer, address=self.p2pkh_address),
        )
        self.assertEqual(
            "J8eojIhqVBXWAIRRLwl1wOQyPeAwGlZgbGwcDXH+kNlbFhbJPS4eWW5cDwFgIkgna9u2hZ1TS9iUuVjyCKpNm9c=",
            self.provider.sign_message(self.message, self.signer, address=self.p2wpkh_address),
        )
        self.assertEqual(
            "I8eojIhqVBXWAIRRLwl1wOQyPeAwGlZgbGwcDXH+kNlbFhbJPS4eWW5cDwFgIkgna9u2hZ1TS9iUuVjyCKpNm9c=",
            self.provider.sign_message(self.message, self.signer, address=self.p2wpkh_p2sh_address),
        )

    def test_verify_message(self):
        self.assertTrue(
            self.provider.verify_message(
                self.p2pkh_address,
                self.message,
                "H8eojIhqVBXWAIRRLwl1wOQyPeAwGlZgbGwcDXH+kNlbFhbJPS4eWW5cDwFgIkgna9u2hZ1TS9iUuVjyCKpNm9c=",
            )
        )
        self.assertTrue(
            self.provider.verify_message(
                self.p2wpkh_address,
                self.message,
                "J8eojIhqVBXWAIRRLwl1wOQyPeAwGlZgbGwcDXH+kNlbFhbJPS4eWW5cDwFgIkgna9u2hZ1TS9iUuVjyCKpNm9c=",
            )
        )
        self.assertTrue(
            self.provider.verify_message(
                self.p2wpkh_p2sh_address,
                self.message,
                "I8eojIhqVBXWAIRRLwl1wOQyPeAwGlZgbGwcDXH+kNlbFhbJPS4eWW5cDwFgIkgna9u2hZ1TS9iUuVjyCKpNm9c=",
            )
        )

    def test_verify_invalid_message(self):
        self.assertFalse(
            self.provider.verify_message(
                "16UwLL9Risc3QfPqBUvKofHmBQ7wMtjvM",
                "foobar",
                "G8JawPtQOrybrSP1WHQnQPr67B9S3qrxBrl1mlzoTJOSHEpmnF7D3+t+LX0Xei9J20B5AIdPbeL3AaTBZ4N3bY0=",
            )
        )
        self.assertFalse(
            self.provider.verify_message(
                "1111111111111111111114oLvT2",
                "vires is numeris"
                "H8JawPtQOrybrSP1WHQnQPr67B9S3qrxBrl1mlzoTJOSHEpmnF7D3+t+LX0Xei9J20B5AIdPbeL3AaTBZ4N3bY0=",
            )
        )
        self.assertFalse(
            self.provider.verify_message(
                "16UwLL9Risc3QfPqBUvKofHmBQ7wMtjvM",
                "vires is numeris",
                "H8JawPtQOrybrSP1WHQnQPr67B9S3qrxBrl1mlzoTJOSHEpmnF7D3+t+LX0Xei9J20B5AIdPbeL3AaTBZ4N3bY0=",
            )
        )
        self.assertFalse(
            self.provider.verify_message(
                "1PMycacnJaSqwwJqjawXBErnLsZ7RkXUAs",
                "vires is numeris",
                "G8JawPtQOrybrSP1WHQnQPr67B9S3qrxBrl1mlzoTJOSHEpmnF7D3+t+LX0Xei9J20B5AIdPbeL3AaTBZ4N3bY0=",
            )
        )
