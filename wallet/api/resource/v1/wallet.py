from falcon.media.validators import jsonschema

from wallet.lib.wallet import manager as wallet_manager


class Collection:
    URI = "wallets"

    def on_get(self, req, resp):
        chain_code, update_balance = req.params.get("chain_code"), req.params.get("update_balance", False)
        resp.media = wallet_manager.get_all_wallets_info(chain_code, update_balance)


class Item:
    URI = Collection.URI + "/{wallet_id}"

    def on_get(self, req, resp, wallet_id):
        update_balance = req.params.get("update_balance", False)
        resp.media = wallet_manager.get_wallet_info_by_id(wallet_id, update_balance=update_balance)


class PreSend:
    URI = Collection.URI + "/{wallet_id}/pre_send"

    @jsonschema.validate(
        {
            "type": "object",
            "required": ["coin_code"],
            "properties": {
                "coin_code": {"type": "string"},
                "to_address": {"type": "string"},
                "value": {"type": "string"},
                "nonce": {"type": "string"},
                "fee_limit": {"type": "string"},
                "fee_price_per_unit": {"type": "string"},
                "payload": {"type": "object"},
            },
        }
    )
    def on_post(self, req, resp, wallet_id):
        media = req.media
        coin_code, to_address, value, nonce, fee_limit, fee_price_per_unit, payload = (
            media["coin_code"],
            media.get("to_address"),
            media.get("value"),
            media.get("nonce"),
            media.get("fee_limit"),
            media.get("fee_price_per_unit"),
            media.get("payload"),
        )

        wallet_id = int(wallet_id)
        value = value and int(value)
        nonce = nonce and int(nonce)
        fee_limit = fee_limit and int(fee_limit)
        fee_price_per_unit = fee_price_per_unit and int(fee_price_per_unit)

        result = wallet_manager.pre_send(
            wallet_id=wallet_id,
            coin_code=coin_code,
            to_address=to_address,
            value=value,
            nonce=nonce,
            fee_limit=fee_limit,
            fee_price_per_unit=fee_price_per_unit,
            payload=payload,
        )
        resp.media = result


class Send:
    URI = Collection.URI + "/{wallet_id}/send"

    @jsonschema.validate(
        {
            "type": "object",
            "required": ["coin_code", "to_address", "value"],
            "properties": {
                "coin_code": {"type": "string"},
                "to_address": {"type": "string"},
                "value": {"type": "string"},
                "nonce": {"type": "string"},
                "fee_limit": {"type": "string"},
                "fee_price_per_unit": {"type": "string"},
                "payload": {"type": "object"},
                "password": {"type": "string"},
                "device_path": {"type": "string"},
            },
        }
    )
    def on_post(self, req, resp, wallet_id):
        media = req.media
        coin_code, to_address, value, nonce, fee_limit, fee_price_per_unit, payload, password, device_path = (
            media["coin_code"],
            media["to_address"],
            media["value"],
            media.get("nonce"),
            media.get("fee_limit"),
            media.get("fee_price_per_unit"),
            media.get("payload"),
            media.get("password"),
            media.get("device_path"),
        )

        wallet_id = int(wallet_id)
        value = int(value)
        nonce = nonce and int(nonce)
        fee_limit = fee_limit and int(fee_limit)
        fee_price_per_unit = fee_price_per_unit and int(fee_price_per_unit)

        result = wallet_manager.send(
            wallet_id=wallet_id,
            coin_code=coin_code,
            to_address=to_address,
            value=value,
            nonce=nonce,
            fee_limit=fee_limit,
            fee_price_per_unit=fee_price_per_unit,
            payload=payload,
            password=password,
            hardware_device_path=device_path,
        )
        resp.media = result
