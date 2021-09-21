from unittest import TestCase
from unittest.mock import Mock, patch

from wallet.lib.basic.request import enums, exceptions, restful


class TestRestfulRequest(TestCase):
    @patch("wallet.lib.basic.request.restful.Session")
    def test_request(self, fake_session_creator):
        fake_session = Mock()
        fake_session_creator.return_value = fake_session

        with self.subTest("Create instance"):
            fake_session_initializer = Mock()
            ins = restful.RestfulRequest(
                "https://www.restful_testing.com", session_initializer=fake_session_initializer
            )

            fake_session.headers.update.assert_called_once_with({"User-Agent": "Tilapia"})
            fake_session_initializer.assert_called_once_with(fake_session)

        with self.subTest("Get error response"):
            fake_response = Mock(ok=False, status_code=504, text="Server Not Ready")
            fake_session.request.return_value = fake_response

            with self.assertRaisesRegex(
                exceptions.ResponseException, "status_code: 504, response_text: Server Not Ready"
            ):
                ins.request(enums.Method.GET, "/api/ping", params={"user": "a"}, headers={"Custom-Field": "cc"})

            fake_session.request.assert_called_once_with(
                method="GET",
                url="https://www.restful_testing.com/api/ping",
                params={"user": "a"},
                data=None,
                json=None,
                headers={"Custom-Field": "cc"},
                timeout=30,
            )
            fake_session.request.reset_mock()

        with self.subTest("Get bad json response"):
            fake_response = Mock(ok=True, status_code=200, text="Bad Json", json=Mock(side_effect=ValueError))
            fake_session.request.return_value = fake_response

            with self.assertRaisesRegex(exceptions.ResponseException, "response_text: Bad Json"):
                ins.request(enums.Method.GET, "/api/ping")

            fake_session.request.assert_called_once_with(
                method="GET",
                url="https://www.restful_testing.com/api/ping",
                params=None,
                data=None,
                json=None,
                headers=None,
                timeout=30,
            )
            fake_session.request.reset_mock()

        with self.subTest("Get normal json as response"):
            fake_response = Mock(ok=True, status_code=200, json=Mock(return_value={"result": "pong"}))
            fake_session.request.return_value = fake_response

            self.assertEqual({"result": "pong"}, ins.request(enums.Method.GET, "/api/ping"))

            fake_session.request.assert_called_once_with(
                method="GET",
                url="https://www.restful_testing.com/api/ping",
                params=None,
                data=None,
                json=None,
                headers=None,
                timeout=30,
            )
            fake_session.request.reset_mock()

        with self.subTest("Get raw response"):
            fake_response = Mock(ok=True, status_code=200, json=Mock(return_value={"result": "pong"}))
            fake_session.request.return_value = fake_response

            ins.response_jsonlize = False
            self.assertEqual(fake_response, ins.request(enums.Method.GET, "/api/ping"))

            fake_session.request.assert_called_once_with(
                method="GET",
                url="https://www.restful_testing.com/api/ping",
                params=None,
                data=None,
                json=None,
                headers=None,
                timeout=30,
            )
            fake_session.request.reset_mock()
