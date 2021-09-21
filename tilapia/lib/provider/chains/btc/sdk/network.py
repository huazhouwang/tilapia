import importlib

from pycoin.networks.registry import network_for_netcode as pycoin_network

from tilapia.lib.coin import codes
from tilapia.lib.conf import settings

code_mapping = {
    codes.TBTC: "xtn",
    **getattr(settings, "my_CODE_MAPPING", {}),
}

custom_networks = {codes.BCH, codes.VTC, codes.NMC, codes.BTG, codes.DASH, codes.DGB}


def get_custom_network(chain_code):
    try:
        module = importlib.import_module(f"tilapia.lib.provider.chains.btc.sdk.custom.{chain_code.lower()}")
        return getattr(module, "network")
    except (AttributeError, ImportError):
        raise ValueError("no network with symbol %s found" % chain_code)


def get_network_by_chain_code(chain_code: str):
    if chain_code in code_mapping:
        chain_code = code_mapping[chain_code]

    if chain_code in custom_networks:
        network = get_custom_network(chain_code)
    else:
        network = pycoin_network(chain_code)

    return network
