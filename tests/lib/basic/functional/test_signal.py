from unittest import TestCase
from unittest.mock import Mock, call

from wallet.lib.basic.functional.signal import Signal


class TestSignal(TestCase):
    def test_signal(self):
        callback = Mock()
        receiver_a = Mock(side_effect=lambda i, j: callback(r="a", s=i + j))
        receiver_b = Mock(side_effect=lambda i, j: callback(r="b", s=i + j))
        receiver_c = Mock(side_effect=lambda i, j: callback(r="c", s=i + j))

        signal = Signal("for_test")
        signal.connect(receiver_a)
        signal.connect(receiver_b)
        signal.connect(receiver_c)

        with self.subTest("the first time"):
            signal.send(i=1, j=2)

            receiver_a.assert_called_once_with(i=1, j=2)
            receiver_b.assert_called_once_with(i=1, j=2)
            receiver_c.assert_called_once_with(i=1, j=2)
            callback.assert_has_calls(
                [
                    call(r="a", s=3),
                    call(r="b", s=3),
                    call(r="c", s=3),
                ]
            )

            receiver_a.reset_mock()
            receiver_b.reset_mock()
            receiver_c.reset_mock()
            callback.reset_mock()

        with self.subTest("drop receiver_a and receiver_c"):
            del receiver_a
            signal.disconnect(receiver_c)

            signal.send(i=2, j=3)
            receiver_b.assert_called_once_with(i=2, j=3)
            callback.assert_called_once_with(r="b", s=5)

            receiver_b.reset_mock()
            callback.reset_mock()

        with self.subTest("no receiver anymore"):
            del receiver_b
            signal.send(i=5, j=4)

            callback.assert_not_called()
