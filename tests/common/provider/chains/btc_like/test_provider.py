from unittest import TestCase
from unittest.mock import Mock

from common.coin import codes
from common.provider import data
from common.provider.chains.bch import BCHProvider
from common.provider.chains.btc import BTCProvider
from common.secret import data as secret_data
from common.secret import manager as secret_manager


class TestBTCLikeCoin(TestCase):
    def _init_provider(self, chain_code: str):
        _encoding = _encodings[chain_code]
        self.fake_chain_info = Mock(
            chain_code=chain_code,
            default_address_encoding=_encoding[0],
            bip44_purpose_options={i: 0 for i in _encoding},
        )
        self.fake_coins_loader = Mock()
        self.fake_client_selector = Mock()

        provider_cls = BCHProvider if chain_code == codes.BCH else BTCProvider

        self.provider = provider_cls(
            chain_info=self.fake_chain_info,
            coins_loader=self.fake_coins_loader,
            client_selector=self.fake_client_selector,
        )

    def _run_fixture(self, fixture_name: str) -> tuple:
        fixture = _fixtures[fixture_name]

        for chain_code, cases in fixture.items():
            with self.subTest(chain_code):
                self._init_provider(chain_code)

                for index, case in enumerate(cases):
                    yield self.subTest(f"{fixture_name}:{chain_code}:Case:{index}"), case

    def test_pubkey_to_address(self):
        for sub_test, case in self._run_fixture("pubkey_to_address"):
            with sub_test:
                (my_key, encoding), result = case
                self.assertEqual(
                    result,
                    self.provider.pubkey_to_address(_get_my_key(my_key), encoding),
                )

    def test_is_valid_address(self):
        for sub_test, case in self._run_fixture("is_valid_address"):
            with sub_test:
                address, (normalized_address, is_valid, encoding) = case
                self.assertEqual(
                    data.AddressValidation(
                        normalized_address=normalized_address,
                        display_address=normalized_address,
                        is_valid=is_valid,
                        encoding=encoding,
                    ),
                    self.provider.verify_address(address),
                )

    def test_sign_transaction(self):
        for sub_test, case in self._run_fixture("sign_transaction"):
            with sub_test:
                unsigned_tx, (txid, raw_tx) = case
                self.assertEqual(
                    data.SignedTx(txid=txid, raw_tx=raw_tx),
                    self.provider.sign_transaction(
                        data.UnsignedTx(
                            inputs=[
                                data.TransactionInput(
                                    address=address,
                                    value=value,
                                    utxo=data.UTXO(txid=prev_txid, vout=vout, value=value),
                                )
                                for prev_txid, vout, value, address, _ in unsigned_tx["inputs"]
                            ],
                            outputs=[
                                data.TransactionOutput(address, value) for address, value in unsigned_tx["outputs"]
                            ],
                            fee_limit=0,  # meaning less here
                            fee_price_per_unit=0,
                            payload=unsigned_tx.get("payload") or dict(),
                        ),
                        {address: _get_my_key(my_key) for _, _, _, address, my_key in unsigned_tx["inputs"]},
                    ),
                )

    def test_sign_message(self):
        for sub_test, case in self._run_fixture("sign_message"):
            with sub_test:
                (message, my_key, address), signature = case
                self.assertEqual(signature, self.provider.sign_message(message, _get_my_key(my_key), address=address))

    def test_verify_message(self):
        for sub_test, case in self._run_fixture("verify_message"):
            with sub_test:
                (address, message, signature), result = case
                self.assertEqual(result, self.provider.verify_message(address, message, signature))


_encodings = {
    codes.BCH: ("P2PKH",),
    codes.LTC: ("P2PKH", "P2WPKH-P2SH", "P2WPKH"),
    codes.DOGE: ("P2PKH",),
    codes.DASH: ("P2PKH",),
    codes.ZEC: ("P2PKH",),
    codes.BTG: ("P2PKH", "P2WPKH-P2SH", "P2WPKH"),
    codes.DGB: ("P2PKH", "P2WPKH-P2SH", "P2WPKH"),
    codes.NMC: ("P2PKH",),
    codes.VTC: ("P2PKH", "P2WPKH-P2SH", "P2WPKH"),
}
_mnemonics = {
    "mnemonic_all": "all all all all all all all all all all all all",
    "mnemonic_12": "alcohol woman abuse must during monitor noble actual mixed trade anger aisle",
    "mnemonic_abandon": "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about",
}
_the_one_prvkey = "0000000000000000000000000000000000000000000000000000000000000001"
_message_hello_onekey = "Hello OneKey"


def _get_my_key(my_key: str):
    if ":" in my_key:
        name, path = my_key.split(":")
        mnemonic = _mnemonics[name]
        seed = secret_manager.mnemonic_to_seed(mnemonic)
        return secret_manager.raw_create_key_by_master_seed(secret_data.CurveEnum.SECP256K1, seed, path)
    else:
        return secret_manager.raw_create_key_by_prvkey(secret_data.CurveEnum.SECP256K1, bytes.fromhex(my_key))


_is_invalid_address = ("", False, None)
_fixtures = {
    "pubkey_to_address": {
        # verify on https://bip39.onekey.so
        codes.BCH: [
            (
                ("mnemonic_abandon:m/44'/145'/0'/0/0", "P2PKH"),
                "bitcoincash:qqyx49mu0kkn9ftfj6hje6g2wfer34yfnq5tahq3q6",
            ),
        ],
        codes.LTC: [
            (
                ("mnemonic_abandon:m/44'/2'/0'/0/0", "P2PKH"),
                "LUWPbpM43E2p7ZSh8cyTBEkvpHmr3cB8Ez",
            ),
            (
                ("mnemonic_abandon:m/49'/2'/0'/0/0", "P2WPKH-P2SH"),
                "M7wtsL7wSHDBJVMWWhtQfTMSYYkyooAAXM",
            ),
            (
                ("mnemonic_abandon:m/84'/2'/0'/0/0", "P2WPKH"),
                "ltc1qjmxnz78nmc8nq77wuxh25n2es7rzm5c2rkk4wh",
            ),
        ],
        codes.DOGE: [
            (
                ("mnemonic_abandon:m/44'/3'/0'/0/0", "P2PKH"),
                "DBus3bamQjgJULBJtYXpEzDWQRwF5iwxgC",
            )
        ],
        codes.DASH: [
            (
                ("mnemonic_abandon:m/44'/5'/0'/0/0", "P2PKH"),
                "XoJA8qE3N2Y3jMLEtZ3vcN42qseZ8LvFf5",
            ),
        ],
        codes.ZEC: [
            (
                ("mnemonic_abandon:m/44'/133'/0'/0/0", "P2PKH"),
                "t1XVXWCvpMgBvUaed4XDqWtgQgJSu1Ghz7F",
            ),
        ],
        codes.BTG: [
            (
                ("mnemonic_abandon:m/44'/156'/0'/0/0", "P2PKH"),
                "GeTZ7bjfXtGsyEcerSSFJNUSZwLfjtCJX9",
            ),
            (
                ("mnemonic_abandon:m/49'/156'/0'/0/0", "P2WPKH-P2SH"),
                "AL8uaqKrP4n61pb2BrQXpMC3VcUdjmpAwn",
            ),
            (
                ("mnemonic_abandon:m/84'/156'/0'/0/0", "P2WPKH"),
                "btg1qkwnu2phwvard2spr2n0a9d84x590ahywl3yacu",
            ),
        ],
        codes.DGB: [
            (
                ("mnemonic_abandon:m/44'/20'/0'/0/0", "P2PKH"),
                "DG1KhhBKpsyWXTakHNezaDQ34focsXjN1i",
            ),
            (
                ("mnemonic_abandon:m/49'/20'/0'/0/0", "P2WPKH-P2SH"),
                "SQ9EXABrHztGgefL9aH3FyeRjowdjtLfn4",
            ),
            (
                ("mnemonic_abandon:m/84'/20'/0'/0/0", "P2WPKH"),
                "dgb1q9gmf0pv8jdymcly6lz6fl7lf6mhslsd72e2jq8",
            ),
        ],
        codes.NMC: [
            (
                ("mnemonic_abandon:m/44'/7'/0'/0/0", "P2PKH"),
                "NEmSxCFhg2zADKaoE4gGP9zgsdgT5ZigyS",
            ),
        ],
        codes.VTC: [
            (
                ("mnemonic_abandon:m/44'/28'/0'/0/0", "P2PKH"),
                "Vce16eJifb7HpuoTFEBJyKNLsBJPo7fM83",
            ),
            (
                ("mnemonic_abandon:m/49'/28'/0'/0/0", "P2WPKH-P2SH"),
                "3GKaSv31kZoxGwMs2Kp25ngoHRHi5pz2SP",
            ),
            (
                ("mnemonic_abandon:m/84'/28'/0'/0/0", "P2WPKH"),
                "vtc1qfe8v6c4r39fq8xnjgcpunt5spdfcxw63zzfwru",
            ),
        ],
    },
    "is_valid_address": {
        codes.BCH: [
            (
                "bitcoincash:qqyx49mu0kkn9ftfj6hje6g2wfer34yfnq5tahq3q6",
                ("bitcoincash:qqyx49mu0kkn9ftfj6hje6g2wfer34yfnq5tahq3q6", True, "P2PKH"),
            ),
            (
                "qqyx49mu0kkn9ftfj6hje6g2wfer34yfnq5tahq3q6",
                ("bitcoincash:qqyx49mu0kkn9ftfj6hje6g2wfer34yfnq5tahq3q6", True, "P2PKH"),
            ),
            ("2MwikwR6hoVijCmr1u8UgzFMHFP6rpQyRvP", _is_invalid_address),
            ("bitcoincash:aqkv9wr69ry2p9l53lxp635va4h86wv435995w8p2h", _is_invalid_address),
            ("bitcoincash:qqqqqqqq9ry2p9l53lxp635va4h86wv435995w8p2h", _is_invalid_address),
            ("22222wR6hoVijCmr1u8UgzFMHFP6rpQyRvP", _is_invalid_address),
            ("155fzsEBHy9Ri2bMQ8uuuR3tv1YzcDywd4", _is_invalid_address),
            ("Hello World!", _is_invalid_address),
            ("bchtest:qpc0qh2xc3tfzsljq79w37zx02kwvzm4gydm222qg8", _is_invalid_address),
        ],
        codes.LTC: [
            ("LUWPbpM43E2p7ZSh8cyTBEkvpHmr3cB8Ez", ("LUWPbpM43E2p7ZSh8cyTBEkvpHmr3cB8Ez", True, "P2PKH")),
            ("M7wtsL7wSHDBJVMWWhtQfTMSYYkyooAAXM", ("M7wtsL7wSHDBJVMWWhtQfTMSYYkyooAAXM", True, "P2WPKH-P2SH")),
            (
                "ltc1qjmxnz78nmc8nq77wuxh25n2es7rzm5c2rkk4wh",
                ("ltc1qjmxnz78nmc8nq77wuxh25n2es7rzm5c2rkk4wh", True, "P2WPKH"),
            ),
        ],
        codes.DOGE: [
            ("DBus3bamQjgJULBJtYXpEzDWQRwF5iwxgC", ("DBus3bamQjgJULBJtYXpEzDWQRwF5iwxgC", True, "P2PKH")),
        ],
        codes.DASH: [
            ("XoJA8qE3N2Y3jMLEtZ3vcN42qseZ8LvFf5", ("XoJA8qE3N2Y3jMLEtZ3vcN42qseZ8LvFf5", True, "P2PKH")),
        ],
        codes.ZEC: [
            ("t1XVXWCvpMgBvUaed4XDqWtgQgJSu1Ghz7F", ("t1XVXWCvpMgBvUaed4XDqWtgQgJSu1Ghz7F", True, "P2PKH")),
        ],
        codes.BTG: [
            ("GeTZ7bjfXtGsyEcerSSFJNUSZwLfjtCJX9", ("GeTZ7bjfXtGsyEcerSSFJNUSZwLfjtCJX9", True, "P2PKH")),
            ("AL8uaqKrP4n61pb2BrQXpMC3VcUdjmpAwn", ("AL8uaqKrP4n61pb2BrQXpMC3VcUdjmpAwn", True, "P2WPKH-P2SH")),
            (
                "btg1qkwnu2phwvard2spr2n0a9d84x590ahywl3yacu",
                ("btg1qkwnu2phwvard2spr2n0a9d84x590ahywl3yacu", True, "P2WPKH"),
            ),
        ],
        codes.DGB: [
            ("DG1KhhBKpsyWXTakHNezaDQ34focsXjN1i", ("DG1KhhBKpsyWXTakHNezaDQ34focsXjN1i", True, "P2PKH")),
            ("SQ9EXABrHztGgefL9aH3FyeRjowdjtLfn4", ("SQ9EXABrHztGgefL9aH3FyeRjowdjtLfn4", True, "P2WPKH-P2SH")),
            (
                "dgb1q9gmf0pv8jdymcly6lz6fl7lf6mhslsd72e2jq8",
                ("dgb1q9gmf0pv8jdymcly6lz6fl7lf6mhslsd72e2jq8", True, "P2WPKH"),
            ),
        ],
        codes.NMC: [
            ("NEmSxCFhg2zADKaoE4gGP9zgsdgT5ZigyS", ("NEmSxCFhg2zADKaoE4gGP9zgsdgT5ZigyS", True, "P2PKH")),
        ],
        codes.VTC: [
            ("Vce16eJifb7HpuoTFEBJyKNLsBJPo7fM83", ("Vce16eJifb7HpuoTFEBJyKNLsBJPo7fM83", True, "P2PKH")),
            ("3GKaSv31kZoxGwMs2Kp25ngoHRHi5pz2SP", ("3GKaSv31kZoxGwMs2Kp25ngoHRHi5pz2SP", True, "P2WPKH-P2SH")),
            (
                "vtc1qfe8v6c4r39fq8xnjgcpunt5spdfcxw63zzfwru",
                ("vtc1qfe8v6c4r39fq8xnjgcpunt5spdfcxw63zzfwru", True, "P2WPKH"),
            ),
        ],
    },
    "sign_transaction": {
        codes.BCH: [
            (
                dict(
                    dec="1 input, 1 output",
                    inputs=[
                        (
                            "f5582709623f2ca01bbdb7f445b77aa98546c5cd507f278ac9f78690c7b0b2ea",
                            3,
                            110000,
                            "bitcoincash:qqyx49mu0kkn9ftfj6hje6g2wfer34yfnq5tahq3q6",
                            "mnemonic_abandon:m/44'/145'/0'/0/0",
                        )
                    ],
                    outputs=[("bitcoincash:qpat6dfpdgyevf0cldkntk5p9txds9gxd5mayx6zan", 109040)],
                ),
                (
                    "12972db35452c095307ac211c077fd772134f3d08ba854968da1e2aff7fcfc60",
                    "0100000001eab2b0c79086f7c98a277f50cdc54685a97ab745f4b7bd1ba02c3f62092758f5030000006a4730440220495da6499b50b5e6ad5dce0ab68a3e219c13806b04880a5bfe25fe8b042a71ba02204d0475cf49ff9eb211e09e81fd2c02c7da6bf9e61e178a1731b4b7eca0f7a0ad412102bbe7dbcdf8b2261530a867df7180b17a90b482f74f2736b8a30d3f756e42e217ffffffff01f0a90100000000001976a9147abd35216a099625f8fb6d35da812accd815066d88ac00000000",
                ),
            ),
            (
                dict(
                    dec="1 input, 1 output, 1 change",
                    inputs=[
                        (
                            "bc37c28dfb467d2ecb50261387bf752a3977d7e5337915071bb4151e6b711a78",
                            0,
                            1995344,
                            "bitcoincash:qzqxk2q6rhy3j9fnnc00m08g4n5dm827xv2dmtjzzp",
                            "mnemonic_12:m/44'/145'/0'/0/0",
                        )
                    ],
                    outputs=[
                        ("bitcoincash:qzh9hc7v8qa2dgx59pylharhp02ps96rputhg7w79h", 1896050),
                        ("bitcoincash:qr23ajjfd9wd73l87j642puf8cad20lfmqdgwvpat4", 73452),
                    ],
                ),
                (
                    "a68be27842bfe9c16f79d77beb3e5f8439b9bbd54851f12d84b0059762cdccec",
                    "0100000001781a716b1e15b41b07157933e5d777392a75bf87132650cb2e7d46fb8dc237bc000000006b483045022100ecaa81efe52d31cb0b9cf49a3a5ef4e4b3c6c6d4379deaa0be7c1d80fa65b44d022035ed7ca3a05d91ec554baab6f0bb2950ca8570887bb2a7252c1cb2e2e523aa1041210322228eeb50bf798b7020df33447086fcb670d4c5bc1b87ba92ac0c86280a7257ffffffff0272ee1c00000000001976a914ae5be3cc383aa6a0d42849fbf4770bd41817430f88acec1e0100000000001976a914d51eca49695cdf47e7f4b55507893e3ad53fe9d888ac00000000",
                ),
            ),
            (
                dict(
                    dec="2 inputs, 1 output, no change",
                    inputs=[
                        (
                            "502e8577b237b0152843a416f8f1ab0c63321b1be7a8cad7bf5c5c216fcf062c",
                            0,
                            1896050,
                            "bitcoincash:qzh9hc7v8qa2dgx59pylharhp02ps96rputhg7w79h",
                            "mnemonic_12:m/44'/145'/0'/1/0",
                        ),
                        (
                            "502e8577b237b0152843a416f8f1ab0c63321b1be7a8cad7bf5c5c216fcf062c",
                            1,
                            73452,
                            "bitcoincash:qrglksfd2ay0zren2ssj7y6dff8kfsgdmg27fwz79p",
                            "mnemonic_12:m/44'/145'/0'/0/1",
                        ),
                    ],
                    outputs=[
                        ("bitcoincash:qq6wnnkrz7ykaqvxrx4hmjvayvzjzml54uyk76arx4", 1934960),
                    ],
                ),
                (
                    "96e1ec90419ac5be0f8b1da68cb3177dcb0bea553e864a036309fb79911acf63",
                    "01000000022c06cf6f215c5cbfd7caa8e71b1b32630cabf1f816a4432815b037b277852e50000000006a4730440220390cfc34868254d1c241ef84af706bd387d3a7bbbc6049a7b99d70cc6f4e62ea022071a820ce96251df00e5a2b9ec2b4f41c813ad5beda3e5a02f605796f066e58c7412102183f94f532d059b1d9b1c13128c0e5153251b697d7d5613382b82e74c08d8514ffffffff2c06cf6f215c5cbfd7caa8e71b1b32630cabf1f816a4432815b037b277852e50010000006b483045022100aba0d278cf9cb86d24f415bbd16c8f2b3e44d8fb517522efe8c7ff45b28428e302206a788e77c2abd24573cc0b899f0c6b923b769f009afd54bb897d33ccafc3e7d3412102f33aeb90a28b991307a1cbad8dbc5da1cd064c2f6c90f9907ec4cef6015acdf3ffffffff0170861d00000000001976a91434e9cec317896e818619ab7dc99d2305216ff4af88ac00000000",
                ),
            ),
            (
                dict(
                    dec="legacy address in output",
                    inputs=[
                        (
                            "502e8577b237b0152843a416f8f1ab0c63321b1be7a8cad7bf5c5c216fcf062c",
                            0,
                            1896050,
                            "bitcoincash:qzh9hc7v8qa2dgx59pylharhp02ps96rputhg7w79h",
                            "mnemonic_12:m/44'/145'/0'/1/0",
                        ),
                        (
                            "502e8577b237b0152843a416f8f1ab0c63321b1be7a8cad7bf5c5c216fcf062c",
                            1,
                            73452,
                            "bitcoincash:qrglksfd2ay0zren2ssj7y6dff8kfsgdmg27fwz79p",
                            "mnemonic_12:m/44'/145'/0'/0/1",
                        ),
                    ],
                    outputs=[
                        ("15pnEDZJo3ycPUamqP3tEDnEju1oW5fBCz", 1934960),
                    ],
                ),
                (
                    "96e1ec90419ac5be0f8b1da68cb3177dcb0bea553e864a036309fb79911acf63",
                    "01000000022c06cf6f215c5cbfd7caa8e71b1b32630cabf1f816a4432815b037b277852e50000000006a4730440220390cfc34868254d1c241ef84af706bd387d3a7bbbc6049a7b99d70cc6f4e62ea022071a820ce96251df00e5a2b9ec2b4f41c813ad5beda3e5a02f605796f066e58c7412102183f94f532d059b1d9b1c13128c0e5153251b697d7d5613382b82e74c08d8514ffffffff2c06cf6f215c5cbfd7caa8e71b1b32630cabf1f816a4432815b037b277852e50010000006b483045022100aba0d278cf9cb86d24f415bbd16c8f2b3e44d8fb517522efe8c7ff45b28428e302206a788e77c2abd24573cc0b899f0c6b923b769f009afd54bb897d33ccafc3e7d3412102f33aeb90a28b991307a1cbad8dbc5da1cd064c2f6c90f9907ec4cef6015acdf3ffffffff0170861d00000000001976a91434e9cec317896e818619ab7dc99d2305216ff4af88ac00000000",
                ),
            ),
        ],
        codes.LTC: [
            (
                dict(
                    dec="one input, one output",
                    inputs=[
                        (
                            "ea06a5b8d3c059da8b319ec6046d5387416e26236072751ced45a055c1fb649f",
                            0,
                            798400,
                            "LVuDpNCSSj6pQ7t9Pv6d6sUkLKoqDEVUnJ",
                            _the_one_prvkey,
                        )
                    ],
                    outputs=[("MR8UQSBr5ULwWheBHznrHk2jxyxkHQu8vB", 798150)],
                    payload=dict(op_return="Litecoin to the MOOOOOON!"),
                ),
                (
                    "55bf49cfa783fb54dd5228fd3a427c68ae0d845c1a7c8245186526e5a2858580",
                    "01000000019f64fbc155a045ed1c75726023266e4187536d04c69e318bda59c0d3b8a506ea000000006a47304402207d7fc1e06acfedeb7f0d4dac2f500277a02de32ecda65a07ca217d987c78195802201d726f21ce6d45ab0da82b43204241c7ccac748de796db31108e15d2b1601d3e01210279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798ffffffff02c62d0c000000000017a914bcfeb728b584253d5f3f70bcb780e9ef218a68f48700000000000000001b6a194c697465636f696e20746f20746865204d4f4f4f4f4f4f4e2100000000",
                ),
            ),
            (
                dict(
                    dec="(P2WPKH-P2SH): one input, one output",
                    inputs=[
                        (
                            "55bf49cfa783fb54dd5228fd3a427c68ae0d845c1a7c8245186526e5a2858580",
                            0,
                            798150,
                            "MR8UQSBr5ULwWheBHznrHk2jxyxkHQu8vB",
                            _the_one_prvkey,
                        )
                    ],
                    outputs=[("ltc1qw508d6qejxtdg4y5r3zarvary0c5xw7kgmn4n9", 797900)],
                    payload=dict(op_return="Litecoin to the MOOOOOON!"),
                ),
                (
                    "1573a69a27cc8c938e404244b827d952c2505ba53835aa8c71a5ca92c5b0ea4a",
                    "01000000000101808585a2e526651845827c1a5c840dae687c423afd2852dd54fb83a7cf49bf550000000017160014751e76e8199196d454941c45d1b3a323f1433bd6ffffffff02cc2c0c0000000000160014751e76e8199196d454941c45d1b3a323f1433bd600000000000000001b6a194c697465636f696e20746f20746865204d4f4f4f4f4f4f4e210247304402207cefb1ea02fbf86527f84f293cf17ae3493c74233fa3cd1d7329d332725dff7e0220487a7c66d129a5ea91a904b850a6dacefd22bfe5a3978ac5116227e577a6682101210279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f8179800000000",
                ),
            ),
            (
                dict(
                    dec="(P2WPKH): one input, one output",
                    inputs=[
                        (
                            "19b8ce3cead41e371bd35548dd13b4a1df172830e6516650a6eaece981e51c7f",
                            0,
                            796700,
                            "ltc1qw508d6qejxtdg4y5r3zarvary0c5xw7kgmn4n9",
                            _the_one_prvkey,
                        )
                    ],
                    outputs=[("ltc1qq6hag67dl53wl99vzg42z8eyzfz2xlkvz9zn23", 796500)],
                    payload=dict(op_return="Litecoin to the MOOOOOON!"),
                ),
                (
                    "cc62444e1520ff3e64a4b1bb5d5704e5d8d0dfac143e3702f9b833bb5e51c17c",
                    "010000000001017f1ce581e9eceaa6506651e6302817dfa1b413dd4855d31b371ed4ea3cceb8190000000000ffffffff0254270c000000000016001406afd46bcdfd22ef94ac122aa11f241244a37ecc00000000000000001b6a194c697465636f696e20746f20746865204d4f4f4f4f4f4f4e210247304402204705aa56a3769d95f740e1c68203a22256e950666e6bb322cfb5d48b57b4f67a0220353390bdbe5824c84bf7635f709f5791e778280c17c7c56b94820cf091f97f2501210279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f8179800000000",
                ),
            ),
        ],
        codes.DOGE: [
            (
                dict(
                    dec="1 input, 1 output",
                    inputs=[
                        (
                            "18ee4ea8bdab52075a8000cd24a7419db842a2b9a473cf920e286d3411179297",
                            0,
                            200000000,
                            "DFpN6QqFfUm3gKNaxN6tNcab1FArL9cZLE",
                            _the_one_prvkey,
                        )
                    ],
                    outputs=[("D6gX4oG51ktj8jWDUvFT81pYHsKk67EC5h", 100000000)],
                ),
                (
                    "e652370dc898b1cdfcd971422f7fa8eb4af5387212a90807c8a6172a6101d29f",
                    "010000000197921711346d280e92cf73a4b9a242b89d41a724cd00805a0752abbda84eee18000000006a473044022019b858d1bd54d9f4be56a3ab1616b2fbd98f56b08e46e3797a81724e0a1def3702202b9f112125074118d1a10f3e225e8639ccbfa68c5148f4aff5cd1507b996886601210279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798ffffffff0100e1f505000000001976a91410e97e8c9b89f2e7e5e5f426dd0923f3a16ca40c88ac00000000",
                ),
            ),
        ],
        codes.DASH: [
            (
                dict(
                    dec="1 input, 1 output, no change",
                    inputs=[
                        (
                            "24522992fb42f85d2d43efa3a1ddb98de23ed28583e19128e6e200a9fa6bc665",
                            1,
                            1000000,
                            "XdTw4G5AWW4cogGd7ayybyBNDbuB45UpgH",
                            "mnemonic_all:m/44'/5'/0'/0/0",
                        )
                    ],
                    outputs=[("XnD5rf5CsAo68wr2h9Nod58whcxX94VvqQ", 998060)],
                ),
                (
                    "be1af4a0e1eaccf86767836b42ee0938cceba16d0dd6c283f476db692c961f41",
                    "010000000165c66bfaa900e2e62891e18385d23ee28db9dda1a3ef432d5df842fb92295224010000006a473044022061db2e7970f5cc6a8bbd1547103f28558e36177862e8fc13ea5b69dd199b52560220277451bb5ce650a95e5f67019ca0ddaa1fef221310c52bd1919e54a5caae5b4b012102936f80cac2ba719ddb238646eb6b78a170a55a52a9b9f08c43523a4a6bd5c896ffffffff01ac3a0f00000000001976a9147e6191bd0404cb41ed67e041bd674e2a5c9d280188ac00000000",
                ),
            ),
            (
                dict(
                    dec="dip2 input",
                    inputs=[
                        (
                            "15575a1c874bd60a819884e116c42e6791c8283ce1fc3b79f0d18531a61bbb8a",
                            1,
                            4095000260,
                            "XdTw4G5AWW4cogGd7ayybyBNDbuB45UpgH",
                            "mnemonic_all:m/44'/5'/0'/0/0",
                        )
                    ],
                    outputs=[
                        ("Xync2SwkGgAtnm2JZcFNWnM5hXoMxS4o2L", 4000000000),
                        ("XrEFMNkxeipYHgEQKiJuqch8XzwrtfH5fm", 95000000),
                    ],
                ),
                (
                    "1477821a1337cd0c625b2442c2a15e00bf10bc7cc44cca853db1260995200d86",
                    "01000000018abb1ba63185d1f0793bfce13c28c891672ec416e18498810ad64b871c5a5715010000006b483045022100f0442b6d9c7533cd6f74afa993b280ed9475276d69df4dac631bc3b5591ba71b022051daf125372c1c477681bbd804a6445d8ff6840901854fb0b485b1c6c7866c44012102936f80cac2ba719ddb238646eb6b78a170a55a52a9b9f08c43523a4a6bd5c896ffffffff0200286bee000000001976a914fd61dd017dad1f505c0511142cc9ac51ef3a5beb88acc095a905000000001976a914aa7a6a1f43dfc34d17e562ce1845b804b73fc31e88ac00000000",
                ),
            ),
            (
                dict(
                    dec="special input",
                    inputs=[
                        (
                            "adb43bcd8fc99d6ed353c30ca8e5bd5996cd7bcf719bd4253f103dfb7227f6ed",
                            0,
                            167280961,
                            "XdTw4G5AWW4cogGd7ayybyBNDbuB45UpgH",
                            "mnemonic_all:m/44'/5'/0'/0/0",
                        )
                    ],
                    outputs=[("XkNPrBSJtrHZUvUqb3JF4g5rMB3uzaJfEL", 167000000)],
                ),
                (
                    "3043f58487eb1ad4f4411fabcf3c4b560f2af4cbd514dabb004963ec39712b84",
                    "0100000001edf62772fb3d103f25d49b71cf7bcd9659bde5a80cc353d36e9dc98fcd3bb4ad000000006b483045022100f7f940f5e3ca4cbe5d787d2dfb121dc56cd224da647b17a170e5e03b29e68744022002cc9d9d6b203180d1f68e64ba8a73fd9e983cca193b7bcf94e0156ed245bdfa012102936f80cac2ba719ddb238646eb6b78a170a55a52a9b9f08c43523a4a6bd5c896ffffffff01c037f409000000001976a9146a341485a9444b35dc9cb90d24e7483de7d37e0088ac00000000",
                ),
            ),
        ],
        codes.ZEC: [
            (
                dict(
                    dec="input v2, no change",
                    inputs=[
                        (
                            "29d25589db4623d1a33c58745b8f95b131f49841c79dcd171847d0d7e9e2dc3a",
                            0,
                            80000,
                            "t1Lv2EguMkaZwvtFQW5pmbUsBw59KfTEhf4",
                            "mnemonic_all:m/44'/133'/0'/0/0",
                        )
                    ],
                    outputs=[("t1N5zTV5PjJqRgSPmszHopk88Nc6mvMBSD7", 72200)],
                ),
                (
                    "0f762a2da5252d684fb3510a3104bcfb556fab34583b3b0e1994d0f7409cc075",
                    "01000000013adce2e9d7d0471817cd9dc74198f431b1958f5b74583ca3d12346db8955d229000000006b483045022100f36da2fba65831c24bae2264892d914abdf65ee747ba9e8deeaeb13d1c72b03102200b8ecb59698dbe90f8cfe529a6d05c8b7fa2f31a2f5a7a1b993700a20d04d63a0121022f5c53b6d2e1b64c37d85716dbef318bd398ad7d2a03d94960af060402380658ffffffff01081a0100000000001976a9142e383c56fe3df202792e6f4460c8056b6a4d5b3488ac00000000",
                ),
            ),
            (
                dict(
                    dec="inputs v1, no change",
                    inputs=[
                        (
                            "84533aa6244bcee68040d851dc4f502838ed3fd9ce838e2e48dbf440e7f4df2a",
                            0,
                            13123,
                            "t1ggDXKaRa1ibmiAJT5WTYF7sYbj23PGN1c",
                            "mnemonic_all:m/44'/133'/0'/0/2",
                        ),
                        (
                            "84533aa6244bcee68040d851dc4f502838ed3fd9ce838e2e48dbf440e7f4df2a",
                            1,
                            3299,
                            "t1bnnLaQAKnCgJhvWYYPbSsL7bbV3uCRzzH",
                            "mnemonic_all:m/44'/133'/0'/1/0",
                        ),
                    ],
                    outputs=[("t1Xin4H451oBDwrKcQeY1VGgMWivLs2hhuR", 10212)],
                ),
                (
                    "e5229ae8c02f74af5e0c2100371710424fa85902c29752498c39921de2246824",
                    "01000000022adff4e740f4db482e8e83ced93fed3828504fdc51d84080e6ce4b24a63a5384000000006a473044022066a25c3b0fe18b17327f6080d9e5a26a880cf6ae6c47ff9b7bf9f8a59ab36814022065e4abcdff6f84311ac120b689e5a69db80312446731ab8fe1b3026e29c11ede0121032fd3a554fc321693de4b7cf66649da7726c4d0d3849a7b947774e04d54e38f91ffffffff2adff4e740f4db482e8e83ced93fed3828504fdc51d84080e6ce4b24a63a5384010000006a473044022009fb8f5c4a3ad7960f64a573084b7dec2b73bbe7044328ff05cb6106153014ef022035ab922f75a7c0ff07acd7e99b2469551ce7ff5b830c102d38d175bf3fa8ab74012102a1eb5e72ebdf2a6650593167a4c8391d9a37c2df19e1034fd0e4dc5b525696e9ffffffff01e4270000000000001976a91497e66840d01e615bdcea4a39a1b3afd0a27e6b0188ac00000000",
                ),
            ),
        ],
        codes.BTG: [
            (
                dict(
                    dec="1 input, 1 output, 1 change",
                    inputs=[
                        (
                            "25526bf06c76ad3082bba930cf627cdd5f1b3cd0b9907dd7ff1a07e14addc985",
                            0,
                            1252382934,
                            "GNz6gdeoVdEPbnEcQvWwcHJAHswrAbJpCD",
                            "mnemonic_12:m/44'/156'/0'/0/0",
                        )
                    ],
                    outputs=[
                        ("GPbJXif5oFDHMPfwhq2MkMe8xQPUoTjqhx", 1896050),
                        ("GfDB1tvjfm3bukeoBTtfNqrJVFohS2kCTe", 1250485884),
                    ],
                ),
                (
                    "7c506e07566b5729a5cd0170898a77acf21defdd428ab7728fecb50efb22e94e",
                    "010000000185c9dd4ae1071affd77d90b9d03c1b5fdd7c62cf30a9bb8230ad766cf06b5225000000006a4730440220199a1d14abaf2cc756ec0edfd1e59399225b181aa869a9fc6777f74ffad6744f0220560e79fddd50d3d3a6ad5ad4d079d052345b6c0452124864286a72e88810fc044121021659b2309dcfb7ff4b88e2dc1a18471fca2aa3da64d1c85515fabcc82904d476ffffffff0272ee1c00000000001976a9143f0cf98e116e3a4049c7e78f05f1e935802df01088ac7ce6884a000000001976a914ea5f904d195079a350b534db4446433b3cec222e88ac00000000",
                ),
            ),
            (
                dict(
                    dec="2 inputs, 1 output, no change",
                    inputs=[
                        (
                            "25526bf06c76ad3082bba930cf627cdd5f1b3cd0b9907dd7ff1a07e14addc985",
                            0,
                            1252382934,
                            "GPbJXif5oFDHMPfwhq2MkMe8xQPUoTjqhx",
                            "mnemonic_12:m/44'/156'/0'/1/0",
                        ),
                        (
                            "db77c2461b840e6edbe7f9280043184a98e020d9795c1b65cb7cef2551a8fb18",
                            0,
                            38448607,
                            "GMVb1H7v4siz6Wq9nTHcdNXS8aCyMFM214",
                            "mnemonic_12:m/44'/156'/0'/1/1",
                        ),
                    ],
                    outputs=[("GfDB1tvjfm3bukeoBTtfNqrJVFohS2kCTe", 1270830541)],
                ),
                (
                    "aa72074080b9d1149c59891e6c47b85bcf3cb5de84ac772ae7faf9d1958276c6",
                    "010000000285c9dd4ae1071affd77d90b9d03c1b5fdd7c62cf30a9bb8230ad766cf06b5225000000006a47304402203ae0f1c4188035a26507833679208f7ad577c4812bbba2ed50c54666ac386bfc022059be1525cd142dc709d5f7a1577e90b243e712460374b524d979b200422eef67412102cf2b28fa22872ab35cb6e0728b51fb4c5d18e99284d030bc64b890859c645d5dffffffff18fba85125ef7ccb651b5c79d920e0984a18430028f9e7db6e0e841b46c277db000000006b4830450221009c85769f815dd4c0fdeb6c7c6a2ec0a20b5aaf2be1e67e06ee0ff31bf9b8847202204fba481222bbbc70a4d1412bdfa2acc4e215a63080b0ee16bd163d79f99be8f94121025a639d0293154eecd7afc45dce239f2bc387c3c45b3844ee98eda272fd32d7aeffffffff01cd55bf4b000000001976a914ea5f904d195079a350b534db4446433b3cec222e88ac00000000",
                ),
            ),
            (
                dict(
                    dec="(P2WPKH-P2SH): 1 input, 2 outputs, no change",
                    inputs=[
                        (
                            "25526bf06c76ad3082bba930cf627cdd5f1b3cd0b9907dd7ff1a07e14addc985",
                            0,
                            1252382934,
                            "AezEZUpcgVmtEXhB4uXFfguV64o2a9Bf5h",
                            "mnemonic_12:m/49'/156'/0'/1/0",
                        )
                    ],
                    outputs=[
                        ("GfDB1tvjfm3bukeoBTtfNqrJVFohS2kCTe", 12300000),
                        ("GZFLExxrvWFuFT1xRzhfwQWSE2bPDedBfn", 1240071934),
                    ],
                ),
                (
                    "9d5733644487a0ac8eaeaaf80591cd1a2330ac69e7475557bb98d973a48eee34",
                    "0100000000010185c9dd4ae1071affd77d90b9d03c1b5fdd7c62cf30a9bb8230ad766cf06b52250000000017160014bcf764faafca9982aba3612eb91370d091cddb4affffffff02e0aebb00000000001976a914ea5f904d195079a350b534db4446433b3cec222e88acfefee949000000001976a914a8f757819ec6779409f45788f7b4a0e8f51ec50488ac024730440220666b06c1bd8d3cc899ef95dccebeab394833c52bc13cb94074926e88e879936202201d0d0abda057f2e4244b1de913cb771d0e77f612aa305e73933e3c5d402fbb91412103e4c2e99d4d9a36f949e947d94391d01bd016826afd87132b3257a660139b3b8a00000000",
                ),
            ),
            (
                dict(
                    dec="(P2WPKH-P2SH): 1 input, 1output, 1 change",
                    inputs=[
                        (
                            "25526bf06c76ad3082bba930cf627cdd5f1b3cd0b9907dd7ff1a07e14addc985",
                            0,
                            1252382934,
                            "AezEZUpcgVmtEXhB4uXFfguV64o2a9Bf5h",
                            "mnemonic_12:m/49'/156'/0'/1/0",
                        )
                    ],
                    outputs=[
                        ("GfDB1tvjfm3bukeoBTtfNqrJVFohS2kCTe", 12300000),
                        ("AezEZUpcgVmtEXhB4uXFfguV64o2a9Bf5h", 1240071934),
                    ],
                ),
                (
                    "356e81a0b90882189a2ff19d8afa50d420a3f2d5a1c839cede77acbefa2dda11",
                    "0100000000010185c9dd4ae1071affd77d90b9d03c1b5fdd7c62cf30a9bb8230ad766cf06b52250000000017160014bcf764faafca9982aba3612eb91370d091cddb4affffffff02e0aebb00000000001976a914ea5f904d195079a350b534db4446433b3cec222e88acfefee9490000000017a914fea1579ecdf0e50674819c9924fcc0007e7ec12b8702483045022100b494a98cf4f715432ae007b1bf43a6c918dfaf7a13257e8513422a4559451da9022036490ed9cd6f1aa418739a4c1df9b4b034287046456715daa74cd7c67c5c1fd0412103e4c2e99d4d9a36f949e947d94391d01bd016826afd87132b3257a660139b3b8a00000000",
                ),
            ),
        ],
        codes.DGB: [
            (
                dict(
                    dec="one input, one output, one change",
                    inputs=[
                        (
                            "be150359df4123b379f1f12de978bfced92644645da17b97c7613879f4306a90",
                            15,
                            480000000,
                            "DLA4uzW4TC3eKHLwWY39egmKBVhoFnPYa5",
                            "mnemonic_all:m/44'/20'/0'/0/0",
                        )
                    ],
                    outputs=[
                        ("DPYgaFJcv75poY4n8zYM7gJqb8xVv2zCY3", 200000000),
                        ("DUUeWHbVqFx5afRbqNFKJH4Fz2kqh232Bk", 279954200),
                    ],
                ),
                (
                    "5bdf34a7e473606c44a1fd783a3753ba9b33d03db5c7c1de6b5e6d823f4f3786",
                    "0100000001906a30f4793861c7977ba15d644426d9cebf78e92df1f179b32341df590315be0f0000006a47304402204128edbb3916f9382e1315707c128f6cab21254ae03ef90454a74595b6fe09d102202588c2ddbebeb280a58cdfa902ac832b83950903a2fed91ab83f7dab486c728001210360d624f82deaa7abd6af3887d36dc4c3ba6d5816de3caed89ba1d142d5f44406ffffffff0200c2eb0b000000001976a914c9e83ddb371ffd7f7049d63e88f37d42636d171b88ac18c3af10000000001976a914fffd7aed2461ca6ba66b1db2c2cf7bae75ae984588ac00000000",
                ),
            ),
            (
                dict(
                    dec="(P2WPKH-P2SH): one input, one output, one change",
                    inputs=[
                        (
                            "be150359df4123b379f1f12de978bfced92644645da17b97c7613879f4306a90",
                            8,
                            480000000,
                            "SgbK2hJXBUccpQgj41fR4VMZqVPesPZgzC",
                            "mnemonic_all:m/49'/20'/0'/0/0",
                        )
                    ],
                    outputs=[
                        ("DPYgaFJcv75poY4n8zYM7gJqb8xVv2zCY3", 100000000),
                        ("SRrevBM5bfZNpFJ4MhzaNfkTghYKoTB6LV", 379976060),
                    ],
                ),
                (
                    "f898dfba870d1b25267b4bb0235f96fd45ffd0b34a4b5d337b695c72853c9abb",
                    "01000000000101906a30f4793861c7977ba15d644426d9cebf78e92df1f179b32341df590315be08000000171600140e19b50b2c3308cb7ca0ce62638b844792f26a29ffffffff0200e1f505000000001976a914c9e83ddb371ffd7f7049d63e88f37d42636d171b88ac7cf9a5160000000017a914320d7056c33fd8d0f5bb9cf42d74133dc28d89bb8702483045022100ca35368081bcc80a0cbb67de19a661afb83f508f7d2a899031190e754ea73382022054c1feb8d49e89d7d1f6c0b6fc4b78ccdcb327aeb099e1bba5826b9ea777380b01210373a23c3c02382ce1e4911c4719a30accf9338c3fb166908726472c203db4224f00000000",
                ),
            ),
        ],
        codes.NMC: [
            (
                dict(
                    dec="one input, one output",
                    inputs=[
                        (
                            "4d49a71ec9da436f71ec4ee231d04f292a29cd316f598bb7068feccabdc59485",
                            0,
                            100210,
                            "N7FdkoPbHSxKfrSVVbRu3NZtrLqc1oKpAR",
                            _the_one_prvkey,
                        )
                    ],
                    outputs=[("N5Tk6cvP91f2Cbb72PoKKMMLTuKTXZ6w7c", 100000)],
                ),
                (
                    "c8607b9cca8c9ab45224d7c6a53e4d80986d048aa3c1dfd6058a52fe9e8db3b9",
                    "01000000018594c5bdcaec8f06b78b596f31cd292a294fd031e24eec716f43dac91ea7494d000000006b483045022100940e17d617c17aa05664b1503ff4606c81045ab2d2724cd58f4731c30299071a022030a5b703e4839e48d0bb8b27cdd0c4796b8af6c25710044ac5b03487873279a301210279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798ffffffff01a0860100000000001976a91461787f8d57b6c0127e174c2189d35e7dfabc0d1a88ac00000000",
                ),
            ),
        ],
        codes.VTC: [
            (
                dict(
                    dec="one input, one output",
                    inputs=[
                        (
                            "4d49a71ec9da436f71ec4ee231d04f292a29cd316f598bb7068feccabdc59485",
                            0,
                            100210,
                            "Vkg6Ts44mskyD668xZkxFkjqovjXX9yUzZ",
                            _the_one_prvkey,
                        )
                    ],
                    outputs=[("Vi3D144NqsgQrX855wZACv1j8F8fWin1NM", 100000)],
                ),
                (
                    "a584f40125490eb39ec50244847dff6d3fb9b989dd77cd80429a2d3dcf426355",
                    "01000000018594c5bdcaec8f06b78b596f31cd292a294fd031e24eec716f43dac91ea7494d000000006b483045022100cb7031444bccbfa8e4f1fe2a32f68dcae849b51f0ad2643af507060a2853ddf802207f34425e2ba3a74911d008d3bd1eb10f27004203d1b37cc67f2b9c644766b7c601210279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798ffffffff01a0860100000000001976a9145834479edbbe0539b31ffd3a8f8ebadc2165ed0188ac00000000",
                ),
            ),
        ],
    },
    "sign_message": {
        codes.BCH: [
            (
                (
                    _message_hello_onekey,
                    "mnemonic_abandon:m/44'/145'/0'/0/0",
                    "bitcoincash:qqyx49mu0kkn9ftfj6hje6g2wfer34yfnq5tahq3q6",
                ),
                "HyLTe+Di9J2sopxrwxL9wA0SQU8VU28wwLMyXpOJ59gvs8U2/c00iGCPjwiZUoAojD0dHGViWlOc6Bqi4FM7vrA=",
            ),
        ],
        codes.LTC: [
            (
                (
                    _message_hello_onekey,
                    "mnemonic_abandon:m/44'/2'/0'/0/0",
                    "LUWPbpM43E2p7ZSh8cyTBEkvpHmr3cB8Ez",
                ),
                "IGRvRxlizy6X6uAqgCg9Uk50Ehan+OEzFpuAcqF7HXJkJnCGc+KWn4CGVkZ/ERP/SXsXSLwgGIg9zLaqqe1E5cg=",
            ),
            (
                (
                    _message_hello_onekey,
                    "mnemonic_abandon:m/49'/2'/0'/0/0",
                    "M7wtsL7wSHDBJVMWWhtQfTMSYYkyooAAXM",
                ),
                "JPtmQraaSmvjJz8KRhFbI9HPkAdpjltP16SmOdOyy6+3aJ5GbO9hRzeD9/rQalCK7ZecYfEnLGDDSuoYpn9D584=",
            ),
            (
                (
                    _message_hello_onekey,
                    "mnemonic_abandon:m/84'/2'/0'/0/0",
                    "ltc1qjmxnz78nmc8nq77wuxh25n2es7rzm5c2rkk4wh",
                ),
                "Jwm4FlQCcejOtb8ZttumHjtMmN0eDPo+TXrAvL7+BadsdzbwdZQ2PBmmlk/j6DhsJS+Em0KYqsfA+A/rrbOCfCY=",
            ),
        ],
        codes.DOGE: [
            (
                (
                    _message_hello_onekey,
                    "mnemonic_abandon:m/44'/3'/0'/0/0",
                    "DBus3bamQjgJULBJtYXpEzDWQRwF5iwxgC",
                ),
                "HyeaCcrWKzWFfmpxONo1SAfFQYh6cl4i4WNB8Is6JEdPRvasdvi1UlMs2r6G8qw58HiCsmTxKb4P+KYTL2PxpYY=",
            ),
        ],
        codes.DASH: [
            (
                (_message_hello_onekey, "mnemonic_abandon:m/44'/5'/0'/0/0", "XoJA8qE3N2Y3jMLEtZ3vcN42qseZ8LvFf5"),
                "Hzi/0wC7lDM/Pc4Y2WvqaOsN74MBypklfV6ubRaKjZHfmH+uuFB52kqWGRQf9aJ4Cb8VtIX4jsWO2pdb5aF4pC4=",
            )
        ],
        codes.ZEC: [
            (
                (
                    _message_hello_onekey,
                    "mnemonic_abandon:m/44'/133'/0'/0/0",
                    "t1XVXWCvpMgBvUaed4XDqWtgQgJSu1Ghz7F",
                ),
                "HwO2DjhnAtHDKASdojMOnMJH2c8y4ZfV8KIAzEQ7G6ZnX7w6YZrYXeINbU79JeswrFg8fyvWd+VGLPqSUKz9wWE=",
            ),
        ],
        codes.BTG: [
            (
                (_message_hello_onekey, "mnemonic_abandon:m/44'/156'/0'/0/0", "GeTZ7bjfXtGsyEcerSSFJNUSZwLfjtCJX9"),
                "IDezzSCuhCfuBwvwMlHPgTheJ5ogh4QV/s9SbC1KwW4ubXWSEshjcQZgtVsX1fvknaX1UXVxpdjs81DFao2ETnc=",
            ),
            (
                (_message_hello_onekey, "mnemonic_abandon:m/49'/156'/0'/0/0", "AL8uaqKrP4n61pb2BrQXpMC3VcUdjmpAwn"),
                "JBkZZw2L2AWGIhqKu6yiOfM/J6qR7NLviqQt9LFo2Zdeq+hUO/8OlZyMHVrOwkznto2C6FY6lWMIBtUBcevv9Zk=",
            ),
            (
                (
                    _message_hello_onekey,
                    "mnemonic_abandon:m/84'/156'/0'/0/0",
                    "btg1qkwnu2phwvard2spr2n0a9d84x590ahywl3yacu",
                ),
                "Jw5O+2SMOa5mwGao+e5RQRLORsMLFS1JL8i0MSKL1kmFi0MuybpQ9ug7HZjfORzgJnXfU0eVo0rN9BE+4UhLn7E=",
            ),
        ],
        codes.DGB: [
            (
                (_message_hello_onekey, "mnemonic_abandon:m/44'/20'/0'/0/0", "DG1KhhBKpsyWXTakHNezaDQ34focsXjN1i"),
                "IMXTcVxn2WQ6MRk2mHvdXDZRKhUHTAdSkDwF53MlEzRVaIPYIQARjIUEbfhI8eyzQaeVa7oYkbutUZvgOP7rWhU=",
            ),
            (
                (_message_hello_onekey, "mnemonic_abandon:m/49'/20'/0'/0/0", "SQ9EXABrHztGgefL9aH3FyeRjowdjtLfn4"),
                "JLRZLfFOjoWEgE6BD5axjy31mU3oISEiuv0WVcZ1OnVbRQz0oAyPCu96rVV6GJ8bx3JaoD4Ht9ILTNzcnq3Ns9U=",
            ),
            (
                (
                    _message_hello_onekey,
                    "mnemonic_abandon:m/84'/20'/0'/0/0",
                    "dgb1q9gmf0pv8jdymcly6lz6fl7lf6mhslsd72e2jq8",
                ),
                "KD2qQTHBoU522YXQbpjn5ipH4Ar3Lt/l7aXjHdDshFsJHKeJJjFE9xhb+OA7UUJYbmnQX+dDlj0tC+2UyfwxICk=",
            ),
        ],
        codes.NMC: [
            (
                (_message_hello_onekey, "mnemonic_abandon:m/44'/7'/0'/0/0", "NEmSxCFhg2zADKaoE4gGP9zgsdgT5ZigyS"),
                "INEqPzqe7ucj8b6R8kKC9m60YwXWPAaYRh3SJ6NJQifkBTMNfBnEMecExNbkIMGlvE46Ak3fi65VI25dhqAH364=",
            ),
        ],
        codes.VTC: [
            (
                (_message_hello_onekey, "mnemonic_abandon:m/44'/28'/0'/0/0", "Vce16eJifb7HpuoTFEBJyKNLsBJPo7fM83"),
                "IJkXqx5E5MgOkcANAJpmRvJ1n6cJMzxurXbHWy+ir2yGUHptG45UJ9SVV2Dg3zhszHShkQdl74eb/XsT3nu0BBI=",
            ),
            (
                (_message_hello_onekey, "mnemonic_abandon:m/49'/28'/0'/0/0", "3GKaSv31kZoxGwMs2Kp25ngoHRHi5pz2SP"),
                "JK6v861CQd3BQk+Ou/V2wywzJiQ2zB40aNCNIYc2RufElzvxIgxr7xEhAezHonQPcqks3fMUEE31CbQS4vYB/i0=",
            ),
            (
                (
                    _message_hello_onekey,
                    "mnemonic_abandon:m/84'/28'/0'/0/0",
                    "vtc1qfe8v6c4r39fq8xnjgcpunt5spdfcxw63zzfwru",
                ),
                "KIImC+JU83gU2pc8wO5up5gBE2Zbsg8MQJGc1+CPHvcPz9F6m3VBqBPm20Frug82LD/mvcy2aHWfXw+/o+AS+3E=",
            ),
        ],
    },
    "verify_message": {
        codes.BCH: [
            (
                (
                    "bitcoincash:qqyx49mu0kkn9ftfj6hje6g2wfer34yfnq5tahq3q6",
                    _message_hello_onekey,
                    "ICLTe+Di9J2sopxrwxL9wA0SQU8VU28wwLMyXpOJ59gvTDrJAjLLd59wcPdmrX/Xcn2RwIFM7kye17e7rHz6gpE=",
                ),
                True,
            ),
            (
                (
                    "bitcoincash:qqyx49mu0kkn9ftfj6hje6g2wfer34yfnq5tahq3q6",
                    _message_hello_onekey,
                    "HyLTe+Di9J2sopxrwxL9wA0SQU8VU28wwLMyXpOJ59gvs8U2/c00iGCPjwiZUoAojD0dHGViWlOc6Bqi4FM7vrA=",
                ),
                True,
            ),
        ],
        codes.LTC: [
            (
                (
                    "LUWPbpM43E2p7ZSh8cyTBEkvpHmr3cB8Ez",
                    _message_hello_onekey,
                    "IGRvRxlizy6X6uAqgCg9Uk50Ehan+OEzFpuAcqF7HXJkJnCGc+KWn4CGVkZ/ERP/SXsXSLwgGIg9zLaqqe1E5cg=",
                ),
                True,
            ),
            (
                (
                    "M7wtsL7wSHDBJVMWWhtQfTMSYYkyooAAXM",
                    _message_hello_onekey,
                    "JPtmQraaSmvjJz8KRhFbI9HPkAdpjltP16SmOdOyy6+3aJ5GbO9hRzeD9/rQalCK7ZecYfEnLGDDSuoYpn9D584=",
                ),
                True,
            ),
            (
                (
                    "ltc1qjmxnz78nmc8nq77wuxh25n2es7rzm5c2rkk4wh",
                    _message_hello_onekey,
                    "Jwm4FlQCcejOtb8ZttumHjtMmN0eDPo+TXrAvL7+BadsdzbwdZQ2PBmmlk/j6DhsJS+Em0KYqsfA+A/rrbOCfCY=",
                ),
                True,
            ),
        ],
        codes.DOGE: [
            (
                (
                    "DBus3bamQjgJULBJtYXpEzDWQRwF5iwxgC",
                    _message_hello_onekey,
                    "HyeaCcrWKzWFfmpxONo1SAfFQYh6cl4i4WNB8Is6JEdPRvasdvi1UlMs2r6G8qw58HiCsmTxKb4P+KYTL2PxpYY=",
                ),
                True,
            ),
        ],
        codes.DASH: [
            (
                (
                    "XoJA8qE3N2Y3jMLEtZ3vcN42qseZ8LvFf5",
                    _message_hello_onekey,
                    "IDi/0wC7lDM/Pc4Y2WvqaOsN74MBypklfV6ubRaKjZHfZ4BRR6+GJbVp5uvgCl2H9PuZKGC2udqs5TsCpy69nRM=",
                ),
                True,
            ),
            (
                (
                    "XoJA8qE3N2Y3jMLEtZ3vcN42qseZ8LvFf5",
                    _message_hello_onekey,
                    "Hzi/0wC7lDM/Pc4Y2WvqaOsN74MBypklfV6ubRaKjZHfmH+uuFB52kqWGRQf9aJ4Cb8VtIX4jsWO2pdb5aF4pC4=",
                ),
                True,
            ),
        ],
        codes.ZEC: [
            (
                (
                    "t1XVXWCvpMgBvUaed4XDqWtgQgJSu1Ghz7F",
                    _message_hello_onekey,
                    "HwO2DjhnAtHDKASdojMOnMJH2c8y4ZfV8KIAzEQ7G6ZnX7w6YZrYXeINbU79JeswrFg8fyvWd+VGLPqSUKz9wWE=",
                ),
                True,
            ),
        ],
        codes.BTG: [
            (
                (
                    "GeTZ7bjfXtGsyEcerSSFJNUSZwLfjtCJX9",
                    _message_hello_onekey,
                    "IDezzSCuhCfuBwvwMlHPgTheJ5ogh4QV/s9SbC1KwW4ubXWSEshjcQZgtVsX1fvknaX1UXVxpdjs81DFao2ETnc=",
                ),
                True,
            ),
            (
                (
                    "AL8uaqKrP4n61pb2BrQXpMC3VcUdjmpAwn",
                    _message_hello_onekey,
                    "IxkZZw2L2AWGIhqKu6yiOfM/J6qR7NLviqQt9LFo2ZdeVBerxADxamNz4qUxPbMYSC0r9JB0sz0zuP1dGuRGS6g=",
                ),
                True,
            ),
            (
                (
                    "btg1qkwnu2phwvard2spr2n0a9d84x590ahywl3yacu",
                    _message_hello_onekey,
                    "KA5O+2SMOa5mwGao+e5RQRLORsMLFS1JL8i0MSKL1kmFdLzRNkWvCRfE4mcgxuMf2ETPiZ8ZpVVty8Efq4fqoZA=",
                ),
                True,
            ),
            (
                (
                    "AL8uaqKrP4n61pb2BrQXpMC3VcUdjmpAwn",
                    _message_hello_onekey,
                    "JBkZZw2L2AWGIhqKu6yiOfM/J6qR7NLviqQt9LFo2Zdeq+hUO/8OlZyMHVrOwkznto2C6FY6lWMIBtUBcevv9Zk=",
                ),
                True,
            ),
            (
                (
                    "btg1qkwnu2phwvard2spr2n0a9d84x590ahywl3yacu",
                    _message_hello_onekey,
                    "Jw5O+2SMOa5mwGao+e5RQRLORsMLFS1JL8i0MSKL1kmFi0MuybpQ9ug7HZjfORzgJnXfU0eVo0rN9BE+4UhLn7E=",
                ),
                True,
            ),
        ],
        codes.DGB: [
            (
                (
                    "DG1KhhBKpsyWXTakHNezaDQ34focsXjN1i",
                    _message_hello_onekey,
                    "IMXTcVxn2WQ6MRk2mHvdXDZRKhUHTAdSkDwF53MlEzRVaIPYIQARjIUEbfhI8eyzQaeVa7oYkbutUZvgOP7rWhU=",
                ),
                True,
            ),
            (
                (
                    "SQ9EXABrHztGgefL9aH3FyeRjowdjtLfn4",
                    _message_hello_onekey,
                    "JLRZLfFOjoWEgE6BD5axjy31mU3oISEiuv0WVcZ1OnVbRQz0oAyPCu96rVV6GJ8bx3JaoD4Ht9ILTNzcnq3Ns9U=",
                ),
                True,
            ),
            (
                (
                    "dgb1q9gmf0pv8jdymcly6lz6fl7lf6mhslsd72e2jq8",
                    _message_hello_onekey,
                    "KD2qQTHBoU522YXQbpjn5ipH4Ar3Lt/l7aXjHdDshFsJHKeJJjFE9xhb+OA7UUJYbmnQX+dDlj0tC+2UyfwxICk=",
                ),
                True,
            ),
        ],
        codes.NMC: [
            (
                (
                    "NEmSxCFhg2zADKaoE4gGP9zgsdgT5ZigyS",
                    _message_hello_onekey,
                    "INEqPzqe7ucj8b6R8kKC9m60YwXWPAaYRh3SJ6NJQifkBTMNfBnEMecExNbkIMGlvE46Ak3fi65VI25dhqAH364=",
                ),
                True,
            ),
        ],
        codes.VTC: [
            (
                (
                    "Vce16eJifb7HpuoTFEBJyKNLsBJPo7fM83",
                    _message_hello_onekey,
                    "IJkXqx5E5MgOkcANAJpmRvJ1n6cJMzxurXbHWy+ir2yGUHptG45UJ9SVV2Dg3zhszHShkQdl74eb/XsT3nu0BBI=",
                ),
                True,
            ),
            (
                (
                    "3GKaSv31kZoxGwMs2Kp25ngoHRHi5pz2SP",
                    _message_hello_onekey,
                    "I66v861CQd3BQk+Ou/V2wywzJiQ2zB40aNCNIYc2RufEaMQO3fOUEO7e/hM4XYvwjBGB/vObOFJGth5Lqdo0QxQ=",
                ),
                True,
            ),
            (
                (
                    "vtc1qfe8v6c4r39fq8xnjgcpunt5spdfcxw63zzfwru",
                    _message_hello_onekey,
                    "J4ImC+JU83gU2pc8wO5up5gBE2Zbsg8MQJGc1+CPHvcPMC6FZIq+V+wZJL6URfDJ0nrIHxn44CqcYMKe6PAjRdA=",
                ),
                True,
            ),
            (
                (
                    "3GKaSv31kZoxGwMs2Kp25ngoHRHi5pz2SP",
                    _message_hello_onekey,
                    "JK6v861CQd3BQk+Ou/V2wywzJiQ2zB40aNCNIYc2RufElzvxIgxr7xEhAezHonQPcqks3fMUEE31CbQS4vYB/i0=",
                ),
                True,
            ),
            (
                (
                    "vtc1qfe8v6c4r39fq8xnjgcpunt5spdfcxw63zzfwru",
                    _message_hello_onekey,
                    "KIImC+JU83gU2pc8wO5up5gBE2Zbsg8MQJGc1+CPHvcPz9F6m3VBqBPm20Frug82LD/mvcy2aHWfXw+/o+AS+3E=",
                ),
                True,
            ),
        ],
    },
}
