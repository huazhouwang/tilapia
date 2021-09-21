from falcon.media.validators import jsonschema

from tilapia.lib.wallet import manager as wallet_manager


class _Provider:
    URI = "provider/{chain_code}"


class MessageVerifier:
    URI = _Provider.URI + "/message/verify"

    @jsonschema.validate(
        {
            "type": "object",
            "required": ["address", "message", "signature"],
            "properties": {
                "address": {"type": "string"},
                "message": {"type": "string"},
                "signature": {"type": "string"},
                "device_path": {"type": "string"},
            },
        }
    )
    def on_post(self, req, resp, chain_code):
        address, message, signature, device_path = (
            req.media["address"],
            req.media["message"],
            req.media["signature"],
            req.media.get("device_path"),
        )
        resp.media = wallet_manager.verify_message(
            chain_code, address, message, signature, hardware_device_path=device_path
        )
