from unittest import TestCase
from unittest.mock import call, patch

from common.hardware import exceptions
from common.hardware.callbacks import helper


class TestHelper(TestCase):
    @patch("common.hardware.callbacks.helper.set_value_to_agent")
    @patch("common.hardware.callbacks.helper.get_value_of_agent")
    @patch("common.hardware.callbacks.helper.time")
    def test_require_specific_value_of_agent(self, fake_time, fake_get_value_of_agent, fake_set_value_to_agent):
        timestamp = 1599999999

        def fake_time_func():
            nonlocal timestamp
            timestamp += 1
            return timestamp

        fake_time.time.side_effect = fake_time_func

        def fake_get_value_of_agent_func(attr_name):
            nonlocal timestamp

            if attr_name != "my_attr" or timestamp < 1600000030:
                return None
            else:
                return "my_value"

        fake_get_value_of_agent.side_effect = fake_get_value_of_agent_func

        with helper.require_specific_value_of_agent("my_attr", 101) as waiting_input:
            fake_set_value_to_agent.assert_has_calls(
                [
                    call("user_cancel", None),
                    call("my_attr", None),
                    call("code", "101"),
                ]
            )
            fake_set_value_to_agent.reset_mock()

            self.assertEqual("my_value", waiting_input())
            self.assertEqual(31, fake_time.time.call_count)

        fake_set_value_to_agent.assert_has_calls(
            [
                call("user_cancel", None),
                call("my_attr", None),
                call("code", None),
            ]
        )

    @patch("common.hardware.callbacks.helper.set_value_to_agent")
    @patch("common.hardware.callbacks.helper.get_value_of_agent")
    @patch("common.hardware.callbacks.helper.time")
    def test_require_specific_value_of_agent__timeout(
        self, fake_time, fake_get_value_of_agent, fake_set_value_to_agent
    ):
        timestamp = 1599999999

        def fake_time_func():
            nonlocal timestamp
            timestamp += 1
            return timestamp

        fake_time.time.side_effect = fake_time_func

        def fake_get_value_of_agent_func(attr_name):
            nonlocal timestamp

            if attr_name != "my_attr" or timestamp < 1600000030:
                return None
            else:
                return "my_value"

        fake_get_value_of_agent.side_effect = fake_get_value_of_agent_func

        with helper.require_specific_value_of_agent("my_attr", 101) as waiting_input:
            fake_set_value_to_agent.assert_has_calls(
                [
                    call("user_cancel", None),
                    call("my_attr", None),
                    call("code", "101"),
                ]
            )
            fake_set_value_to_agent.reset_mock()

            with self.assertRaises(exceptions.CallbackTimeout):
                self.assertEqual("my_value", waiting_input(30))

            self.assertEqual(31, fake_time.time.call_count)

        fake_set_value_to_agent.assert_has_calls(
            [
                call("user_cancel", None),
                call("my_attr", None),
                call("code", None),
            ]
        )
