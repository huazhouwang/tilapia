from unittest import TestCase
from unittest.mock import Mock, patch

from wallet.lib.basic.ticker.utils import on_interval


class TestUtils(TestCase):
    @patch("wallet.lib.basic.ticker.utils.time")
    def test_on_interval(self, fake_time):
        timestamps = [1600000061, 1600000060, 1600000000]
        fake_time.time.side_effect = timestamps.pop

        callback = Mock()
        func = on_interval(seconds=60)(callback)

        with self.subTest("First time"):
            func(a=1, b=2)
            callback.assert_called_once_with(a=1, b=2)
            callback.reset_mock()

        with self.subTest("Within the time buffer"):
            func(a=1, b=2)
            callback.assert_not_called()

        with self.subTest("Out of time buffer"):
            func(a=2, b=3)
            callback.assert_called_once_with(a=2, b=3)

        self.assertEqual(3, fake_time.time.call_count)
        self.assertEqual(0, len(timestamps))
