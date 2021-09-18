from unittest import TestCase

from common.secret import registry
from common.secret.data import CurveEnum
from common.secret.interfaces import KeyInterface


class TestKeys(TestCase):
    def test_keys(self):
        prvkey_bytes = bytes([11]) * 32
        digests = [bytes([i]) * 32 for i in range(1, 12)]

        for i, (curve, key_class) in enumerate(registry.KEY_CLASS_MAPPING.items()):
            with self.subTest(f"Case-{i}-{curve}"):
                self.assertTrue(issubclass(key_class, KeyInterface))
                self.assertEqual(key_class, registry.key_class_on_curve(curve))

                prvkey: KeyInterface = key_class(prvkey=prvkey_bytes)
                self.assertTrue(prvkey.has_prvkey())
                self.assertEqual(prvkey_bytes, prvkey.get_prvkey())

                if curve in (CurveEnum.SECP256K1, CurveEnum.SECP256R1):
                    self.assertEqual(33, len(prvkey.get_pubkey()))
                    self.assertEqual(33, len(prvkey.get_pubkey(compressed=True)))
                    self.assertEqual(65, len(prvkey.get_pubkey(compressed=False)))
                elif curve == CurveEnum.ED25519:
                    self.assertEqual(32, len(prvkey.get_pubkey()))
                    self.assertEqual(32, len(prvkey.get_pubkey(compressed=True)))  # compressed field has no effect
                    self.assertEqual(32, len(prvkey.get_pubkey(compressed=False)))

                pubkey: KeyInterface = key_class(pubkey=prvkey.get_pubkey())
                self.assertEqual(pubkey.get_pubkey(), prvkey.get_pubkey())
                self.assertEqual(pubkey.get_pubkey(compressed=True), prvkey.get_pubkey(compressed=True))
                self.assertEqual(pubkey.get_pubkey(compressed=False), prvkey.get_pubkey(compressed=False))

                for j, digest in enumerate(digests):
                    with self.subTest(f"Case-{i}-{curve}-Digest-{j}"):
                        signature, recid = prvkey.sign(digest)
                        self.assertTrue(recid in range(4))
                        self.assertTrue(prvkey.verify(digest, signature))
                        self.assertTrue(pubkey.verify(digest, signature))

                        with self.assertRaisesRegex(Exception, "Private key not found"):
                            pubkey.sign(digest)

                error_signature = bytes([11]) * 64
                self.assertFalse(prvkey.verify(bytes([11]) * 32, error_signature))
                self.assertFalse(pubkey.verify(bytes([11]) * 32, error_signature))
