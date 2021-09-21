from falcon.media.validators import jsonschema

from tilapia.lib.price import manager as price_manager


class Price:
    URI = "price"

    @jsonschema.validate(
        {
            "type": "object",
            "required": ["pairs"],
            "properties": {
                "pairs": {"type": "array"},
            },
        }
    )
    def on_post(self, req, resp):
        pairs = req.media.get("pairs", ())

        result = [price_manager.get_last_price(coin_code, unit) for coin_code, unit in pairs]
        resp.media = result
