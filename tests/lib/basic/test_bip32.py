from unittest import TestCase

from wallet.lib.basic import bip32


class TestBip32(TestCase):
    def test_decode_bip44_path(self):
        self.assertEqual([], bip32.decode_bip44_path(""))
        self.assertEqual([], bip32.decode_bip44_path("m"))
        self.assertEqual([], bip32.decode_bip44_path("/"))
        self.assertEqual([], bip32.decode_bip44_path("m/"))
        self.assertEqual([], bip32.decode_bip44_path("m//"))
        self.assertEqual([1, 2, 3], bip32.decode_bip44_path("m/1/2/3"))
        self.assertEqual([2147483649, 2147483650, 3], bip32.decode_bip44_path("m/1'/2'/3"))
        self.assertEqual([2147483649, 2147483650, 3], bip32.decode_bip44_path("1'/2'/3"))

        with self.assertRaisesRegex(ValueError, "bip32 path child index out of range"):
            bip32.decode_bip44_path("-1")

        with self.assertRaisesRegex(ValueError, "bip32 path child index out of range"):
            bip32.decode_bip44_path(f"{1 << 32}")

    def test_encode_bip44_path(self):
        self.assertEqual("m/1'/2'/3", bip32.encode_bip32_path([2147483649, 2147483650, 3]))
        self.assertEqual("m/1/2/3", bip32.encode_bip32_path([1, 2, 3]))

        with self.assertRaisesRegex(ValueError, "bip32 path child index out of range"):
            bip32.encode_bip32_path([-1])

        with self.assertRaisesRegex(ValueError, "bip32 path child index out of range"):
            bip32.encode_bip32_path([1 << 32])
