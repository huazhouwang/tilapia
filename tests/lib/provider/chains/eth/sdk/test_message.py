import json
from unittest import TestCase

from wallet.lib.provider.chains.eth.sdk import message as message_sdk
from wallet.lib.provider.chains.eth.sdk import utils


def _to_bytes(hex_str: str) -> bytes:
    return bytes.fromhex(utils.remove_0x_prefix(hex_str))


def _eip712_v4_testcases():
    return [
        (
            "Type data",
            "0xbe609aee343fb3c4b28e1df9e632fca64fcfaede20f02e86244efddf30957bd2",
            '{"types":{"EIP712Domain":[{"name":"name","type":"string"},{"name":"version","type":"string"},{"name":"chainId","type":"uint256"},{"name":"verifyingContract","type":"address"}],"Person":[{"name":"name","type":"string"},{"name":"wallet","type":"address"}],"Mail":[{"name":"from","type":"Person"},{"name":"to","type":"Person"},{"name":"contents","type":"string"}]},"primaryType":"Mail","domain":{"name":"Ether Mail","version":"1","chainId":1,"verifyingContract":"0xCcCCccccCCCCcCCCCCCcCcCccCcCCCcCcccccccC"},"message":{"from":{"name":"Cow","wallet":"0xCD2a3d9F938E13CD947Ec05AbC7FE734Df8DD826"},"to":{"name":"Bob","wallet":"0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB"},"contents":"Hello, Bob!"}}',
        ),
        (
            "Type data - lowercase address",
            "0xbe609aee343fb3c4b28e1df9e632fca64fcfaede20f02e86244efddf30957bd2",
            '{"types":{"EIP712Domain":[{"name":"name","type":"string"},{"name":"version","type":"string"},{"name":"chainId","type":"uint256"},{"name":"verifyingContract","type":"address"}],"Person":[{"name":"name","type":"string"},{"name":"wallet","type":"address"}],"Mail":[{"name":"from","type":"Person"},{"name":"to","type":"Person"},{"name":"contents","type":"string"}]},"primaryType":"Mail","domain":{"name":"Ether Mail","version":"1","chainId":1,"verifyingContract":"0xcccccccccccccccccccccccccccccccccccccccc"},"message":{"from":{"name":"Cow","wallet":"0xcd2a3d9f938e13cd947ec05abc7fe734df8dd826"},"to":{"name":"Bob","wallet":"0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"},"contents":"Hello, Bob!"}}',
        ),
        (
            "Type data with bytes",
            "0xb4aaf457227fec401db772ec22d2095d1235ee5d0833f56f59108c9ffc90fb4b",
            '{"types":{"EIP712Domain":[{"name":"name","type":"string"},{"name":"version","type":"string"},{"name":"chainId","type":"uint256"},{"name":"verifyingContract","type":"address"}],"Person":[{"name":"name","type":"string"},{"name":"wallet","type":"address"}],"Mail":[{"name":"from","type":"Person"},{"name":"to","type":"Person"},{"name":"contents","type":"string"},{"name":"payload","type":"bytes"}]},"primaryType":"Mail","domain":{"name":"Ether Mail","version":"1","chainId":1,"verifyingContract":"0xCcCCccccCCCCcCCCCCCcCcCccCcCCCcCcccccccC"},"message":{"from":{"name":"Cow","wallet":"0xCD2a3d9F938E13CD947Ec05AbC7FE734Df8DD826"},"to":{"name":"Bob","wallet":"0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB"},"contents":"Hello, Bob!","payload":"0x25192142931f380985072cdd991e37f65cf8253ba7a0e675b54163a1d133b8ca"}}',
        ),
        (
            "Type data with recursive types",
            "0x807773b9faa9879d4971b43856c4d60c2da15c6f8c062bd9d33afefb756de19c",
            '{"types":{"EIP712Domain":[{"name":"name","type":"string"},{"name":"version","type":"string"},{"name":"chainId","type":"uint256"},{"name":"verifyingContract","type":"address"}],"Person":[{"name":"name","type":"string"},{"name":"mother","type":"Person"},{"name":"father","type":"Person"}]},"domain":{"name":"Family Tree","version":"1","chainId":1,"verifyingContract":"0xCcCCccccCCCCcCCCCCCcCcCccCcCCCcCcccccccC"},"primaryType":"Person","message":{"name":"Jon","mother":{"name":"Lyanna","father":{"name":"Rickard"}},"father":{"name":"Rhaegar","father":{"name":"Aeris II"}}}}',
        ),
        (
            "Type data with array",
            "0xa85c2e2b118698e88db68a8105b794a8cc7cec074e89ef991cb4f5f533819cc2",
            '{"types":{"EIP712Domain":[{"name":"name","type":"string"},{"name":"version","type":"string"},{"name":"chainId","type":"uint256"},{"name":"verifyingContract","type":"address"}],"Person":[{"name":"name","type":"string"},{"name":"wallets","type":"address[]"}],"Mail":[{"name":"from","type":"Person"},{"name":"to","type":"Person[]"},{"name":"contents","type":"string"}],"Group":[{"name":"name","type":"string"},{"name":"members","type":"Person[]"}]},"domain":{"name":"Ether Mail","version":"1","chainId":1,"verifyingContract":"0xCcCCccccCCCCcCCCCCCcCcCccCcCCCcCcccccccC"},"primaryType":"Mail","message":{"from":{"name":"Cow","wallets":["0xCD2a3d9F938E13CD947Ec05AbC7FE734Df8DD826","0xDeaDbeefdEAdbeefdEadbEEFdeadbeEFdEaDbeeF"]},"to":[{"name":"Bob","wallets":["0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB","0xB0BdaBea57B0BDABeA57b0bdABEA57b0BDabEa57","0xB0B0b0b0b0b0B000000000000000000000000000"]}],"contents":"Hello, Bob!"}}',
        ),
        (
            "Type data with 2d array",
            "0x5370bb332dbe5d922832f1654d01b5d42cbbfd7bb999e939836f4a40a12a8bd4",
            '{"types":{"EIP712Domain":[{"name":"name","type":"string"},{"name":"version","type":"string"},{"name":"chainId","type":"uint256"},{"name":"verifyingContract","type":"address"}],"Person":[{"name":"name","type":"string"},{"name":"wallets","type":"address[]"},{"name":"logo_matrix","type":"int[][]"}],"Mail":[{"name":"from","type":"Person"},{"name":"to","type":"Person[]"},{"name":"contents","type":"string"}],"Group":[{"name":"name","type":"string"},{"name":"members","type":"Person[]"}]},"domain":{"name":"Ether Mail","version":"1","chainId":1,"verifyingContract":"0xCcCCccccCCCCcCCCCCCcCcCccCcCCCcCcccccccC"},"primaryType":"Mail","message":{"from":{"name":"Cow","wallets":["0xCD2a3d9F938E13CD947Ec05AbC7FE734Df8DD826","0xDeaDbeefdEAdbeefdEadbEEFdeadbeEFdEaDbeeF"],"logo_matrix":[[0,255],[-255,-1]]},"to":[{"name":"Bob","wallets":["0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB","0xB0BdaBea57B0BDABeA57b0bdABEA57b0BDabEa57","0xB0B0b0b0b0b0B000000000000000000000000000"],"logo_matrix":[[0,0],[0,0]]}],"contents":"Hello, Bob!"}}',
        ),
    ]


class TestMessageSDK(TestCase):
    def test_hash_message__raw_hex(self):
        self.assertEqual(
            _to_bytes("0x6c69d03412450b174def7d1e48b3bcbbbd8f51df2e76e2c5b3a5d951125be3a9"),
            message_sdk.hash_message("0x6c69d03412450b174def7d1e48b3bcbbbd8f51df2e76e2c5b3a5d951125be3a9"),  #
        )

    def test_hash_message__personal(self):
        self.assertEqual(
            _to_bytes("0xa47b9109fe1a5b6ada254a9fe498dcaa648938974eda3f9001335aa24b49fe7b"),
            message_sdk.hash_message("6c69d03412450b174def7d1e48b3bcbbbd8f51df2e76e2c5b3a5d951125be3a9"),
        )
        self.assertEqual(
            _to_bytes("0x5f35dce98ba4fba25530a026ed80b2cecdaa31091ba4958b99b52ea1d068adad"),
            message_sdk.hash_message("0x"),
        )
        self.assertEqual(
            _to_bytes("0x5e4106618209740b9f773a94c5667b9659a7a4e2691c7c8a78336e9889a6be07"),
            message_sdk.hash_message("0x" + "0" * 63),
        )
        self.assertEqual(
            _to_bytes("0xd87309a295607439d67ad5243462242d36775fa665de60f4e26895808e01389b"),
            message_sdk.hash_message("0x0102"),
        )
        self.assertEqual(
            _to_bytes("0xdf3619f57f8d35a3bc81a171aad15720f9b531a0707bf637ab37f6407a9e725d"),
            message_sdk.hash_message("Hello OneKey"),
        )
        self.assertEqual(
            _to_bytes("0xc3e8ceedfd47fbc9ee91bec4681a1e3a9aab09b7203aaf5c35d86119af6172cb"),
            message_sdk.hash_message(b"Hello OneKey".hex()),
        )
        self.assertEqual(
            _to_bytes("0xdf3619f57f8d35a3bc81a171aad15720f9b531a0707bf637ab37f6407a9e725d"),
            message_sdk.hash_message(utils.add_0x_prefix(b"Hello OneKey".hex())),
        )

    def test_hash_message__eip712_legacy(self):
        with self.subTest("Single value"):
            self.assertEqual(
                _to_bytes("0x14b9f24872e28cc49e72dc104d7380d8e0ba84a3fe2e712704bcac66a5702bd5"),
                message_sdk.hash_message('[{"type":"string","name":"message","value":"Hi, Alice!"}]'),
            )

        with self.subTest("Multiple values"):
            self.assertEqual(
                _to_bytes("0xf7ad23226db5c1c00ca0ca1468fd49c8f8bbc1489bc1c382de5adc557a69c229"),
                message_sdk.hash_message(
                    '[{"type":"string","name":"message","value":"Hi, Alice!"},{"type":"uint8","name":"value","value":10}]'
                ),
            )

        with self.subTest("Bytes"):
            self.assertEqual(
                _to_bytes("0x6c69d03412450b174def7d1e48b3bcbbbd8f51df2e76e2c5b3a5d951125be3a9"),
                message_sdk.hash_message('[{"type":"bytes","name":"message","value":"0xdeadbeaf"}]'),
            )

        with self.subTest("Address"):
            self.assertEqual(
                _to_bytes("0x5b418c432491db89c10a5cae30b033eef42088c59459f9161756b8124653b7bc"),
                message_sdk.hash_message(
                    '[{"type":"string","name":"message","value":"Hi, Alice!"},{"type":"address","name":"wallet","value":"0xCcCCccccCCCCcCCCCCCcCcCccCcCCCcCcccccccC"}]'
                ),
            )

        with self.subTest("Wrong type"):
            with self.assertRaisesRegex(ValueError, "Unsupported or invalid type: 'jocker'"):
                message_sdk.hash_message('[{"type":"jocker","name":"message","value":"Hi, Alice!"}]')

    def test_hash_message__eip712_v3(self):
        cases = _eip712_v4_testcases()
        cases = [(a, b, json.dumps({"__version__": 3, **json.loads(c)})) for a, b, c in cases]

        for case_name, expected, case in cases[:-3]:
            with self.subTest(case_name):
                self.assertEqual(_to_bytes(expected), message_sdk.hash_message(case))

        with self.subTest("Type data with recursive types"):
            self.assertEqual(
                _to_bytes(
                    "0x0f11d777f9a8098d88e3869334a8f1404fd942062c5037045bae4e3b457007bd"
                ),  # The hash result is different from v4
                message_sdk.hash_message(cases[-3][2]),
            )

        with self.subTest("Unsupported type data with array on v3"):
            with self.assertRaisesRegex(ValueError, "Arrays are unimplemented in V3, use V4 extension"):
                message_sdk.hash_message(cases[-2][2])

    def test_hash_message__eip712_v4(self):
        cases = _eip712_v4_testcases()
        for case_name, expected, case in cases:
            with self.subTest(case_name):
                self.assertEqual(_to_bytes(expected), message_sdk.hash_message(case))
