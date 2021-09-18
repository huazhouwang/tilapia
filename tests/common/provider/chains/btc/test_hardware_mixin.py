from unittest import TestCase
from unittest.mock import Mock, patch

from trezorlib import messages as trezor_messages

from common.basic import bip44
from common.provider import data
from common.provider.chains.btc import BTCProvider


class TestBTCHardwareMixin(TestCase):
    def setUp(self) -> None:
        self.fake_chain_info = Mock(
            chain_code="btc",
            default_address_encoding="P2WPKH-P2SH",
            bip44_purpose_options={"P2PKH": 44, "P2WPKH-P2SH": 49, "P2WPKH": 84},
        )
        self.fake_coins_loader = Mock()
        self.fake_client = Mock()
        self.fake_client_selector = Mock(return_value=self.fake_client)
        self.fake_hardware_client = Mock()
        self.provider = BTCProvider(
            chain_info=self.fake_chain_info,
            coins_loader=self.fake_coins_loader,
            client_selector=self.fake_client_selector,
        )

    @patch("common.provider.chains.btc.hardware_mixin.trezor_btc.sign_tx")
    def test_hardware_sign_transaction(self, fake_trezor_sign):
        # Get previous tx
        previous_txid = "f4a073d6359b4dfd78782cc94b40ce000efcd45eb08d81d758ad29e8659b0645"
        previous_raw_tx = "01000000010100000000000000000000000000000000000000000000000000000000000000000000006a473044022037fab31e055ecaa7008d659b7741b88eb110af888007ffb806e0297eb9cb959d02200745f4e13320454d245585e9346a9002fb72201476d635aaa285cbef66b21b4801210279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798ffffffff02e80300000000000017a914bcfeb728b584253d5f3f70bcb780e9ef218a68f487e8030000000000001976a914751e76e8199196d454941c45d1b3a323f1433bd688ac00000000"
        self.fake_client.get_transaction_by_txid.return_value = Mock(raw_tx=previous_raw_tx)

        fake_trezor_sign.return_value = (
            "fake_signature",
            bytes.fromhex(
                "010000000001027a5cd3b3ceb4cae9d89407cea4570f9fb0ceef76a99500c12d99efcb1141fb42000000006b4830450221008317f67e8e5030368ee81810f6470385ba0d1602fbc0cde32900927ca3978e2f0220686d824988db30c33a8dbfbe91de707cfac5d2b78131a8fecb1fc56c840724ff01210279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798ffffffff7a5cd3b3ceb4cae9d89407cea4570f9fb0ceef76a99500c12d99efcb1141fb420100000017160014751e76e8199196d454941c45d1b3a323f1433bd6ffffffff03dc05000000000000160014751e76e8199196d454941c45d1b3a323f1433bd68b0400000000000017a914bcfeb728b584253d5f3f70bcb780e9ef218a68f48700000000000000000e6a0c48656c6c6f204f6e654b6579000247304402202a5dfce171db0acff89d2c7210279c4bc13e29132d55864a2365e3ff0042d0f8022004ddee0a5156f5cfb69db3ba5ef17baabfd395261477948eaf518fff10db73c701210279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f8179800000000"
            ),
        )

        unsigned_tx = data.UnsignedTx(
            inputs=[
                data.TransactionInput(
                    address="1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH",
                    value=1000,
                    utxo=data.UTXO(txid=previous_txid, vout=0, value=1000),
                ),
                data.TransactionInput(
                    address="3JvL6Ymt8MVWiCNHC7oWU6nLeHNJKLZGLN",
                    value=2000,
                    utxo=data.UTXO(txid=previous_txid, vout=1, value=1000),
                ),
            ],
            outputs=[
                data.TransactionOutput(address="bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4", value=1500),
                data.TransactionOutput(
                    address="3JvL6Ymt8MVWiCNHC7oWU6nLeHNJKLZGLN",
                    value=1163,
                    payload=dict(is_change=True, bip44_path="m/49'/0'/0'/0/0"),
                ),
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
            self.provider.hardware_sign_transaction(
                self.fake_hardware_client,
                unsigned_tx,
                {
                    "1BgGZ9tcN4rm9KBzDn7KprQz87SZ26SAMH": bip44.BIP44Path.from_bip44_path("m/44'/0'/0'/0/0"),
                    "3JvL6Ymt8MVWiCNHC7oWU6nLeHNJKLZGLN": bip44.BIP44Path.from_bip44_path("m/49'/0'/0'/0/0"),
                },
            ),
        )
        self.fake_client.get_transaction_by_txid.assert_called_once_with(previous_txid)
        fake_trezor_sign.assert_called_once()
        call_args, call_kwargs = fake_trezor_sign.call_args.args, fake_trezor_sign.call_args.kwargs
        self.assertEqual(self.fake_hardware_client, call_args[0])
        self.assertEqual(self.fake_chain_info.name, call_args[1])
        self.assertEqual(
            [
                trezor_messages.TxInputType(
                    script_type=trezor_messages.InputScriptType.SPENDADDRESS,
                    address_n=[2147483692, 2147483648, 2147483648, 0, 0],
                    prev_hash=bytes.fromhex(previous_txid),
                    prev_index=0,
                    amount=1000,
                ),
                trezor_messages.TxInputType(
                    script_type=trezor_messages.InputScriptType.SPENDP2SHWITNESS,
                    address_n=[2147483697, 2147483648, 2147483648, 0, 0],
                    prev_hash=bytes.fromhex(previous_txid),
                    prev_index=1,
                    amount=1000,
                ),
            ],
            call_args[2],
        )
        self.assertEqual(
            [
                trezor_messages.TxOutputType(
                    amount=1500,
                    script_type=trezor_messages.OutputScriptType.PAYTOADDRESS,
                    address="bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4",
                ),
                trezor_messages.TxOutputType(
                    amount=1163,
                    script_type=trezor_messages.OutputScriptType.PAYTOP2SHWITNESS,
                    address_n=[2147483697, 2147483648, 2147483648, 0, 0],
                ),
                trezor_messages.TxOutputType(
                    amount=0, script_type=trezor_messages.OutputScriptType.PAYTOOPRETURN, op_return_data=b"Hello OneKey"
                ),
            ],
            call_args[3],
        )
        self.assertEqual(
            {
                bytes.fromhex(previous_txid): trezor_messages.TransactionType(
                    version=1,
                    lock_time=0,
                    inputs=[
                        trezor_messages.TxInputType(
                            prev_hash=bytes.fromhex("0000000000000000000000000000000000000000000000000000000000000001"),
                            prev_index=0,
                            script_sig=bytes.fromhex(
                                "473044022037fab31e055ecaa7008d659b7741b88eb110af888007ffb806e0297eb9cb959d02200745f4e13320454d245585e9346a9002fb72201476d635aaa285cbef66b21b4801210279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798"
                            ),
                            sequence=4294967295,
                        )
                    ],
                    bin_outputs=[
                        trezor_messages.TxOutputBinType(
                            amount=1000, script_pubkey=bytes.fromhex("a914bcfeb728b584253d5f3f70bcb780e9ef218a68f487")
                        ),
                        trezor_messages.TxOutputBinType(
                            amount=1000,
                            script_pubkey=bytes.fromhex("76a914751e76e8199196d454941c45d1b3a323f1433bd688ac"),
                        ),
                    ],
                )
            },
            call_kwargs.get("prev_txes"),
        )
        self.assertEqual(1, call_kwargs.get("version"))
