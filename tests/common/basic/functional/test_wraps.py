from unittest import TestCase
from unittest.mock import Mock, patch

from common.basic.functional.wraps import cache_it


class TestWraps(TestCase):
    @patch("common.basic.functional.wraps.time")
    def test_cache_it(self, fake_time):
        fake_callable = Mock(return_value="ping")
        func = cache_it()(fake_callable)

        timestamps = []
        fake_time.time.side_effect = timestamps.pop

        with self.subTest("the first time"):
            timestamps.append(1600000000)

            self.assertEqual("ping", func())

            self.assertEqual(1, fake_time.time.call_count)
            self.assertEqual(0, len(timestamps))
            fake_callable.assert_called_once()

            fake_time.time.reset_mock()
            fake_callable.reset_mock()

        with self.subTest("cache value as expected"):
            timestamps.append(1600000060)

            self.assertEqual("ping", func())

            self.assertEqual(1, fake_time.time.call_count)
            self.assertEqual(0, len(timestamps))
            fake_callable.assert_not_called()

            fake_time.time.reset_mock()

        with self.subTest("cache expired"):
            timestamps.extend((1600000061, 1600000061))

            self.assertEqual("ping", func())

            self.assertEqual(2, fake_time.time.call_count)
            self.assertEqual(0, len(timestamps))
            fake_callable.assert_called_once()

            fake_callable.reset_mock()
            fake_time.time.reset_mock()

        with self.subTest("force update"):
            timestamps.append(1600000062)

            self.assertEqual("ping", func(a=1, b=3, __force_update_cache_it__=True))

            self.assertEqual(1, fake_time.time.call_count)
            self.assertEqual(0, len(timestamps))
            fake_callable.assert_called_once_with(a=1, b=3)

            fake_time.time.reset_mock()
