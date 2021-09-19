from collections import namedtuple
from unittest import TestCase
from unittest.mock import Mock, call, patch

from wallet.lib.basic.functional.timing import timing_logger


class TestTiming(TestCase):
    @patch("wallet.lib.basic.functional.timing.time.time")
    @patch("wallet.lib.basic.functional.timing.uuid.uuid4")
    @patch("wallet.lib.basic.functional.timing.threading.current_thread")
    def test_timing_logger(
        self,
        fake_current_thread,
        fake_uuid,
        fake_time,
    ):
        fake_thread_struct = namedtuple("FakeThread", ["name"])
        fake_current_thread.return_value = fake_thread_struct(name="testing_thread")
        fake_uuid.return_value = Mock(hex="a1b2c3d4e5f6")
        timestamps = [1600010000, 1600000000]
        fake_time.side_effect = timestamps.pop

        fake_callback = Mock()
        fake_logger = Mock()

        timing_logger("testing", logger_func=fake_logger)(fake_callback)(a=1, b=3)

        fake_uuid.assert_called_once()
        fake_current_thread.assert_called_once()
        self.assertEqual(2, fake_time.call_count)
        fake_callback.assert_called_once_with(a=1, b=3)
        fake_logger.assert_has_calls(
            [
                call("TimingLogger<testing, a1b2c3d4, testing_thread>, start timing logger. now: 1600000000"),
                call("TimingLogger<testing, a1b2c3d4, testing_thread>, end timing logger. time_used: 10000s"),
            ]
        )
