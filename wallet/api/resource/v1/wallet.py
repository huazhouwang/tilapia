from falcon.media.validators import jsonschema

from wallet.lib.basic.functional.json import json_stringify
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


class SoftwarePrimaryCreator:
    URI = Collection.URI + "/software/primary/{chain_code}/create"

    @jsonschema.validate(
        {
            "type": "object",
            "required": ["password"],
            "properties": {
                "password": {"type": "string"},
                "mnemonic": {"type": "string"},
                "passphrase": {"type": "string"},
                "mnemonic_strength": {"type": "integer"},
                "name": {"type": "string"},
                "address_encoding": {"type": "string"},
            },
        }
    )
    def on_post(self, req, resp, chain_code):
        media = req.media
        password = media["password"]

        if wallet_manager.has_primary_wallet():
            name, address_encoding = media.get("name"), media.get("address_encoding")

            if not name:
                count = wallet_manager.count_primary_wallet_by_chain(chain_code)
                name = f"{chain_code.upper()}-{count + 1}"

            result = wallet_manager.create_next_derived_primary_wallet(
                chain_code, name, password, address_encoding=address_encoding
            )
        else:
            mnemonic, passphrase, mnemonic_strength = (
                media.get("mnemonic"),
                media.get("passphrase"),
                media.get("mnemonic_strength", 128),
            )
            result = wallet_manager.create_primary_wallets(
                [chain_code],
                password=password,
                mnemonic=mnemonic,
                passphrase=passphrase,
                mnemonic_strength=mnemonic_strength,
            )[0]

        resp.media = result


class SoftwareStandaloneImporter:
    URI = Collection.URI + "/software/standalone/{chain_code}/import"

    @jsonschema.validate(
        {
            "type": "object",
            "required": ["wallet_type", "password", "payload"],
            "properties": {
                "wallet_type": {"type": "string"},
                "password": {"type": "string"},
                "payload": {"type": "object"},
                "name": {"type": "string"},
                "address_encoding": {"type": "string"},
            },
        }
    )
    def on_post(self, req, resp, chain_code):
        media = req.media
        wallet_type, password, payload, name, address_encoding = (
            media["wallet_type"],
            media["password"],
            media["payload"],
            media.get("name"),
            media.get("address_encoding"),
        )

        if not name:
            name = f"IMPORT-{wallet_type}-{chain_code}".upper()

        if wallet_type == "mnemonic":
            mnemonic, passphrase, bip44_path = payload["mnemonic"], payload.get("passphrase"), payload.get("bip44_path")
            result = wallet_manager.import_standalone_wallet_by_mnemonic(
                name,
                chain_code,
                mnemonic,
                password,
                passphrase=passphrase,
                address_encoding=address_encoding,
                bip44_path=bip44_path,
            )
        elif wallet_type == "keystore":
            keystore_json, keystore_password = payload["keystore"], payload["keystore_password"]
            result = wallet_manager.import_standalone_wallet_by_keystore(
                name, chain_code, keystore_json, keystore_password, password, address_encoding=address_encoding
            )
        elif wallet_type == "prvkey":
            prvkey = payload["prvkey"]
            if prvkey.startswith("0x"):
                prvkey = prvkey[2:]

            result = wallet_manager.import_standalone_wallet_by_prvkey(
                name, chain_code, bytes.fromhex(prvkey), password, address_encoding=address_encoding
            )
        elif wallet_type == "pubkey":
            pubkey = payload["pubkey"]
            if pubkey.startswith("0x"):
                pubkey = pubkey[2:]

            result = wallet_manager.import_watchonly_wallet_by_pubkey(
                name, chain_code, bytes.fromhex(pubkey), address_encoding=address_encoding
            )
        elif wallet_type == "address":
            address = payload["address"]
            result = wallet_manager.import_watchonly_wallet_by_address(name, chain_code, address)
        else:
            raise Exception(f"Invalid wallet type: {wallet_type}")

        resp.media = result


class SoftwareExporter:
    URI = Collection.URI + "/software/{wallet_id}/export"

    @jsonschema.validate(
        {
            "type": "object",
            "required": ["password", "dest"],
            "properties": {
                "password": {"type": "string"},
                "dest": {"type": "string"},
            },
        }
    )
    def on_post(self, req, resp, wallet_id):
        wallet_id = int(wallet_id)

        password, dest = req.media["password"], req.media["dest"]

        if dest == "mnemonic":
            m, p = wallet_manager.export_mnemonic(wallet_id, password)
            result = {"mnemonic": m, "passphrase": p}
        elif dest == "prvkey":
            result = wallet_manager.export_prvkey(wallet_id, password)
        elif dest == "keystore":
            result = wallet_manager.export_keystore(wallet_id, password)
            result = json_stringify(result)
        else:
            raise Exception(f"Invalid destination: {dest}")

        resp.media = result
