import json


def decrypt_eth_keystore(keyfile_json: str, keystore_password: str) -> bytes:
    try:
        import eth_account

        return bytes(eth_account.account.Account.decrypt(keyfile_json, keystore_password))
    except (TypeError, KeyError, NotImplementedError, json.decoder.JSONDecodeError) as e:
        raise Exception(f"Invalid keystore. error: {e}") from e
