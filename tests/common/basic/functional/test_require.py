from unittest import TestCase

from common.basic.functional.require import require, require_none, require_not_none


class TestRequire(TestCase):
    def test_require(self):
        self.assertIsNone(require(True is True))

        with self.assertRaisesRegex(AssertionError, "raising by require"):
            require(False is True)

        with self.assertRaisesRegex(AssertionError, "False is not True"):
            require(False is True, "False is not True")

        with self.assertRaisesRegex(ValueError, "1 != 2"):
            require(1 == 2, ValueError("1 != 2"))

    def test_require_not_none(self):
        self.assertEqual(1, require_not_none(1))

        with self.assertRaisesRegex(AssertionError, "require not none but none found"):
            require_not_none(None)

        with self.assertRaisesRegex(AssertionError, "Please input not none value"):
            require_not_none(None, "Please input not none value")

        with self.assertRaisesRegex(ValueError, "Please input not none value"):
            require_not_none(None, ValueError("Please input not none value"))

    def test_require_none(self):
        self.assertIsNone(require_none(None))

        with self.assertRaisesRegex(AssertionError, "require none but 1 found"):
            require_none(1)

        with self.assertRaisesRegex(AssertionError, "Please input none"):
            require_none(1, "Please input none")

        with self.assertRaisesRegex(ValueError, "Please input none"):
            require_none(1, ValueError("Please input none"))
