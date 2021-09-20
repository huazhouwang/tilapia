from falcon.media.validators import jsonschema

from wallet.lib.wallet import data as wallet_data
from wallet.lib.wallet import manager as wallet_manager


class _HardwareWallet:
    URI = "wallets/hardware"


class PrimaryCreator:
    URI = _HardwareWallet.URI + "/primary/{chain_code}/create"

    @jsonschema.validate(
        {
            "type": "object",
            "required": ["device_path"],
            "properties": {
                "device_path": {"type": "string"},
                "name": {"type": "string"},
                "address_encoding": {"type": "string"},
            },
        }
    )
    def on_post(self, req, resp, chain_code):
        media = req.media
        device_path, name, address_encoding = media["device_path"], media.get("name"), media.get("address_encoding")

        if not name:
            count = wallet_manager.count_specific_type_wallets(chain_code, wallet_data.WalletType.HARDWARE_PRIMARY)
            name = f"{chain_code.upper()}-{count + 1}"

        result = wallet_manager.create_next_primary_hardware_wallet(
            name, chain_code, device_path, address_encoding=address_encoding
        )
        resp.media = result


class StandaloneCreator:
    URI = _HardwareWallet.URI + "/standalone/{chain_code}/create"

    @jsonschema.validate(
        {
            "type": "object",
            "required": ["device_path", "bip44_path"],
            "properties": {
                "device_path": {"type": "string"},
                "bip44_path": {"type": "string"},
                "name": {"type": "string"},
                "address_encoding": {"type": "string"},
            },
        }
    )
    def on_post(self, req, resp, chain_code):
        media = req.media
        device_path, bip44_path, name, address_encoding = (
            media["device_path"],
            media["bip44_path"],
            media.get("name"),
            media.get("address_encoding"),
        )

        if not name:
            name = f"HARDWARE-STANDALONE-{chain_code.upper()}"

        result = wallet_manager.create_standalone_hardware_wallet(
            name, chain_code, device_path, bip44_path, address_encoding=address_encoding
        )
        resp.media = result
