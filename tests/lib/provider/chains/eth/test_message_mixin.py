from unittest import TestCase
from unittest.mock import Mock

from wallet.lib.provider.chains.eth import ETHProvider


class TestETHMessageMixin(TestCase):
    def setUp(self) -> None:
        self.fake_chain_info = Mock()
        self.fake_coins_loader = Mock()
        self.fake_client_selector = Mock()
        self.provider = ETHProvider(
            chain_info=self.fake_chain_info,
            coins_loader=self.fake_coins_loader,
            client_selector=self.fake_client_selector,
        )

    def test_sign_message(self):
        fake_signer = Mock(
            sign=Mock(
                return_value=(
                    bytes.fromhex(
                        "fbbe375d1a893ecd6c0b07a9ddab35f652795afba9998d26ca4224c9832e779f0e6f63be32fc52012ed0db1344a57e4a065fe59bb1c87764ede419cd84cdd2f2"
                    ),
                    0,
                )
            )
        )
        self.assertEqual(
            "0xfbbe375d1a893ecd6c0b07a9ddab35f652795afba9998d26ca4224c9832e779f0e6f63be32fc52012ed0db1344a57e4a065fe59bb1c87764ede419cd84cdd2f21b",
            self.provider.sign_message("Hello OneKey", fake_signer),
        )
        fake_signer.sign.assert_called_once_with(
            bytes.fromhex("df3619f57f8d35a3bc81a171aad15720f9b531a0707bf637ab37f6407a9e725d")
        )

    def test_verify_message(self):
        self.assertTrue(
            self.provider.verify_message(
                "0x29c76e6ad8f28bb1004902578fb108c507be341b",
                "Hello OneKey",
                "0xfbbe375d1a893ecd6c0b07a9ddab35f652795afba9998d26ca4224c9832e779f0e6f63be32fc52012ed0db1344a57e4a065fe59bb1c87764ede419cd84cdd2f21b",
            )
        )
        self.assertFalse(
            self.provider.verify_message(
                "0x29c76e6ad8f28bb1004902578fb108c507be341b",
                "Hello OneKey",
                "0x1bbe375d1a893ecd6c0b07a9ddab35f652795afba9998d26ca4224c9832e779f0e6f63be32fc52012ed0db1344a57e4a065fe59bb1c87764ede419cd84cdd2f21b",
            )
        )

    def test_ec_recover(self):
        self.assertEqual(
            "0x29c76e6ad8f28bb1004902578fb108c507be341b",
            self.provider.ec_recover(
                "Hello OneKey",
                "0xfbbe375d1a893ecd6c0b07a9ddab35f652795afba9998d26ca4224c9832e779f0e6f63be32fc52012ed0db1344a57e4a065fe59bb1c87764ede419cd84cdd2f21b",
            ),
        )

        self.assertEqual(
            "0xa7c4a4ed7ebb0386fd5460d150a57e0d490e7463",
            self.provider.ec_recover(
                "Hello OneKey",
                "0x1bbe375d1a893ecd6c0b07a9ddab35f652795afba9998d26ca4224c9832e779f0e6f63be32fc52012ed0db1344a57e4a065fe59bb1c87764ede419cd84cdd2f21b",
            ),
        )
