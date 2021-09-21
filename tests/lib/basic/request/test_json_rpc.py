from unittest import TestCase
from unittest.mock import Mock, patch

from tilapia.lib.basic.request import exceptions, json_rpc


class TestJsonRPCRequest(TestCase):
    @patch("tilapia.lib.basic.request.json_rpc.RestfulRequest")
    def test_call(self, fake_restful_request_creator):
        fake_restful = Mock()
        fake_restful_request_creator.return_value = fake_restful

        with self.subTest("Create instance"):
            fake_session_initializer = Mock()
            ins = json_rpc.JsonRPCRequest("https://www.rpc_testing.com", session_initializer=fake_session_initializer)

            fake_restful_request_creator.assert_called_once_with(
                base_url="https://www.rpc_testing.com",
                timeout=30,
                response_jsonlize=True,
                debug_mode=False,
                session_initializer=fake_session_initializer,
            )

        with self.subTest("Get normal response"):
            fake_restful.post.return_value = {"result": "pong"}

            self.assertEqual(
                "pong", ins.call("ping", params=["a"], headers={"Custom-Field": "cc"}, timeout=10, path="/api")
            )

            fake_restful.post.assert_called_once_with(
                "/api",
                json={"jsonrpc": "2.0", "id": 0, "method": "ping", "params": ["a"]},
                timeout=10,
                headers={"Custom-Field": "cc"},
            )

        with self.subTest("Get illegal type response"):
            fake_restful.post.return_value = "Bad Request"

            with self.assertRaisesRegex(
                exceptions.JsonRPCException, "The RPC response should be a dict, but got <Bad Request>"
            ):
                ins.call("ping")

        with self.subTest("Get error message from response"):
            fake_restful.post.return_value = {"error": "Server Not Ready"}

            with self.assertRaisesRegex(
                exceptions.JsonRPCException, "Error at the RPC response. error: Server Not Ready"
            ):
                ins.call("ping")

        with self.subTest("'result' not found in response"):
            fake_restful.post.return_value = {"_result": "pong"}

            with self.assertRaisesRegex(exceptions.JsonRPCException, "No 'result' found from the RPC response"):
                ins.call("ping")

        with self.subTest("Get error response"):
            fake_restful.post.side_effect = exceptions.RequestException

            with self.assertRaisesRegex(exceptions.JsonRPCException, "Json RPC call failed."):
                ins.call("ping", params=["a"], headers={"Custom-Field": "cc"})

    @patch("tilapia.lib.basic.request.json_rpc.RestfulRequest")
    def test_batch_call(self, fake_restful_request_creator):
        fake_restful = Mock()
        fake_restful_request_creator.return_value = fake_restful

        ins = json_rpc.JsonRPCRequest("https://www.rpc_testing.com")

        with self.subTest("Get normal response"):
            fake_restful.post.return_value = [
                {"id": 1, "result": "pong_b"},
                {"id": 0, "result": "pong_a"},
                {"id": 2, "result": "pong_c"},
            ]
            self.assertEqual(
                ["pong_a", "pong_b", "pong_c"],
                ins.batch_call(
                    [("ping_a", ["param_a"]), ("ping_b", []), ("ping_c", [{"user": "c"}])],
                    headers={"Custom-Field": "cc"},
                    timeout=10,
                    path="/api",
                ),
            )

            fake_restful.post.assert_called_once_with(
                "/api",
                json=[
                    {"jsonrpc": "2.0", "id": 0, "method": "ping_a", "params": ["param_a"]},
                    {"jsonrpc": "2.0", "id": 1, "method": "ping_b", "params": []},
                    {"jsonrpc": "2.0", "id": 2, "method": "ping_c", "params": [{"user": "c"}]},
                ],
                headers={"Custom-Field": "cc"},
                timeout=10,
            )

        with self.subTest("Get illegal type response"):
            fake_restful.post.return_value = {"result": "pong"}
            with self.assertRaisesRegex(
                exceptions.JsonRPCException, "Responses of batch call should be a list, but got <{'result': 'pong'}>"
            ):
                ins.batch_call([("ping_a", []), ("ping_b", []), ("ping_c", [])])

        with self.subTest("Get insufficient response"):
            fake_restful.post.return_value = [{"id": 1, "result": "pong_b"}, {"id": 0, "result": "pong_a"}]

            with self.assertRaisesRegex(exceptions.JsonRPCException, "Batch with 3 calls, but got 2 responses"):
                ins.batch_call([("ping_a", []), ("ping_b", []), ("ping_c", [])])

        with self.subTest("Get error response"):
            fake_restful.post.side_effect = exceptions.RequestException

            with self.assertRaisesRegex(exceptions.JsonRPCException, "Json RPC call failed."):
                ins.batch_call([("ping_a", []), ("ping_b", []), ("ping_c", [])])
