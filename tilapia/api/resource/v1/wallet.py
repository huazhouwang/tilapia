from falcon.media.validators import jsonschema

from tilapia.lib.basic.functional.require import require
from tilapia.lib.coin import manager as coin_manager
from tilapia.lib.wallet import manager as wallet_manager


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

    @jsonschema.validate(
        {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "password": {"type": "string"},
                "new_password": {"type": "string"},
            },
        }
    )
    def on_post(self, req, resp, wallet_id):
        media = req.media
        name, password, new_password = media.get("name"), media.get("password"), media.get("new_password")

        if name:
            wallet_manager.update_wallet_name(wallet_id, name)

        if password:
            require(new_password, "Require 'new_password'")
            wallet_manager.update_wallet_password(wallet_id, password, new_password)

    @jsonschema.validate(
        {
            "type": "object",
            "required": ["password"],
            "properties": {
                "password": {"type": "string"},
            },
        }
    )
    def on_delete(self, req, resp, wallet_id):
        password = req.media["password"]
        wallet_manager.cascade_delete_wallet_related_models(wallet_id, password)


class _Asset:
    URI = Item.URI + "/assets/{coin_code}"


class ShowAsset:
    URI = _Asset.URI + "/show"

    def on_post(self, req, resp, wallet_id, coin_code):
        wallet_manager.create_or_show_asset(wallet_id, coin_code)
        resp.media = coin_manager.get_coin_info(coin_code)


class HideAsset:
    URI = _Asset.URI + "/hide"

    def on_post(self, req, resp, wallet_id, coin_code):
        wallet_manager.hide_asset(wallet_id, coin_code)


class PreSend:
    URI = _Asset.URI + "/pre_send"

    @jsonschema.validate(
        {
            "type": "object",
            "properties": {
                "to_address": {"type": "string"},
                "value": {"type": "string"},
                "nonce": {"type": "string"},
                "fee_limit": {"type": "string"},
                "fee_price_per_unit": {"type": "string"},
                "payload": {"type": "object"},
            },
        }
    )
    def on_post(self, req, resp, wallet_id, coin_code):
        media = req.media
        to_address, value, nonce, fee_limit, fee_price_per_unit, payload = (
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
    URI = _Asset.URI + "/send"

    @jsonschema.validate(
        {
            "type": "object",
            "required": ["to_address", "value"],
            "properties": {
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
    def on_post(self, req, resp, wallet_id, coin_code):
        media = req.media
        to_address, value, nonce, fee_limit, fee_price_per_unit, payload, password, device_path = (
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


class MessageSigner:
    URI = Item.URI + "/message/sign"

    @jsonschema.validate(
        {
            "type": "object",
            "required": ["message"],
            "properties": {
                "password": {"type": "string"},
                "message": {"type": "string"},
                "device_path": {"type": "string"},
            },
        }
    )
    def on_post(self, req, resp, wallet_id):
        message, password, device_path = req.media["message"], req.media.get("password"), req.media.get("device_path")
        resp.media = wallet_manager.sign_message(
            wallet_id, message, password=password, hardware_device_path=device_path
        )


class HardwareAddressConfirm:
    URI = Item.URI + "/confirm_address_on_hardware"

    @jsonschema.validate(
        {
            "type": "object",
            "required": ["device_path"],
            "properties": {
                "device_path": {"type": "string"},
            },
        }
    )
    def on_post(self, req, resp, wallet_id):
        device_path = req.media["device_path"]
        resp.media = wallet_manager.confirm_address_on_hardware(wallet_id, device_path)
