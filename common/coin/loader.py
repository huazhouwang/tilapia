import enum
from typing import Dict, Tuple, Type

from common.basic import bip44
from common.coin import data as coins_data
from common.coin.chains import mainnet, testnet
from common.conf import settings
from common.secret import data as secret_data


def _replace_enum_fields(raw_data: dict, fields: Dict[str, Type[enum.Enum]]):
    for field_name, enum_cls in fields.items():
        if field_name not in raw_data:
            continue

        enum_name = raw_data[field_name].upper()
        enum_ins = enum_cls[enum_name]
        raw_data[field_name] = enum_ins


def _load_config(configs: dict) -> Tuple[Dict[str, coins_data.ChainInfo], Dict[str, coins_data.CoinInfo]]:
    chains, coins = {}, {}

    for chain_config in configs:
        coins_config = chain_config.pop("coins")
        _replace_enum_fields(
            chain_config,
            {
                "chain_model": coins_data.ChainModel,
                "curve": secret_data.CurveEnum,
                "bip44_last_hardened_level": bip44.BIP44Level,
                "bip44_auto_increment_level": bip44.BIP44Level,
                "bip44_target_level": bip44.BIP44Level,
            },
        )

        chain_info = coins_data.ChainInfo(**chain_config)
        chains[chain_info.chain_code] = chain_info
        coins.update({i["code"]: coins_data.CoinInfo(chain_code=chain_info.chain_code, **i) for i in coins_config})

    return chains, coins


_MAINNET_CHAINS, _MAINNET_COINS = _load_config(mainnet.CHAINS)
_TESTNET_CHAINS, _TESTNET_COINS = _load_config(testnet.CHAINS)
_MY_CHAINS, _MY_COINS = _load_config(getattr(settings, "MY_CHAINS", dict()))

CHAINS_DICT = {**_MAINNET_CHAINS, **_TESTNET_CHAINS}
COINS_DICT = {**_MAINNET_COINS, **_TESTNET_COINS}
