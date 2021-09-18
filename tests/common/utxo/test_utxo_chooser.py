from unittest import TestCase

from common.utxo import utxo_chooser


class TestUTXOChooser(TestCase):
    def test_choose(self):
        self.assertEqual([100], utxo_chooser.choose(list(range(1, 101)), 100))
        self.assertEqual([38, 66], utxo_chooser.choose(list(range(1, 101)), 101))
        self.assertEqual(
            [82, 45, 37, 85, 51, 97, 91, 67, 17, 81, 34, 25, 53, 92, 100, 65],
            utxo_chooser.choose(list(range(1, 101)), 1000),
        )
