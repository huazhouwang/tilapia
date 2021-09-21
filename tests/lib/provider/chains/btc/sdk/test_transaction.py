from unittest import TestCase

from tilapia.lib.provider.chains.btc.sdk import transaction


class TestTransaction(TestCase):
    def test_calculate_vsize(self):
        self.assertEqual(79, transaction.calculate_vsize(["P2WPKH"], []))
        self.assertEqual(176, transaction.calculate_vsize(["P2WPKH"], ["P2WPKH", "P2PKH", "P2WPKH-P2SH"]))
        self.assertEqual(255, transaction.calculate_vsize(["P2PKH"], ["P2WPKH", "P2PKH", "P2WPKH-P2SH"]))
        self.assertEqual(199, transaction.calculate_vsize(["P2WPKH-P2SH"], ["P2WPKH", "P2PKH", "P2WPKH-P2SH"]))
        self.assertEqual(246, transaction.calculate_vsize([], [], op_return="a" * 200))
