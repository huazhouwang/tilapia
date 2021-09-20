from falcon.media.validators import jsonschema

from wallet.lib.coin import manager as coin_manager


class Collection:
    URI = "chains"

    def on_get(self, req, resp):
        resp.media = coin_manager.get_all_chains()


class Item:
    URI = Collection.URI + "/{chain_code}"

    def on_get(self, req, resp, chain_code):
        resp.media = coin_manager.get_chain_info(chain_code)


class Coins:
    URI = Item.URI + "/coins"

    def on_get(self, req, resp, chain_code):
        resp.media = coin_manager.get_coins_by_chain(chain_code)


class CoinItem:
    URI = Coins.URI + "/{coin_code}"

    def on_get(self, req, resp, chain_code, coin_code):
        resp.media = coin_manager.get_coin_info(coin_code, nullable=True)


class AddCoin:
    URI = Coins.URI + "/add"

    @jsonschema.validate(
        {
            "type": "object",
            "required": ["token_address", "symbol", "decimals"],
            "properties": {
                "token_address": {"type": "string"},
                "symbol": {"type": "string"},
                "decimals": {"type": "integer"},
                "name": {"type": "string"},
                "icon": {"type": "string"},
            },
        }
    )
    def on_post(self, req, resp, chain_code):
        media = req.media
        token_address, symbol, decimals, name, icon = (
            media["token_address"],
            media["symbol"],
            media["symbol"],
            media.get("name"),
            media.get("icon"),
        )
        coin_code = coin_manager.add_coin(chain_code, token_address, symbol, decimals, name=name, icon=icon)

        resp.media = coin_manager.get_coin_info(coin_code)
