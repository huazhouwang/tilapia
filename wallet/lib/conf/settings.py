import os
from os import environ, path
from typing import Literal

runtime: Literal["host", "terminal"] = "terminal"
if "API_HOSTING" in environ:
    runtime = "host"

IS_DEV = os.environ.get("IS_DEV") == "True"

PROJECT_DIR = path.dirname(path.dirname(path.dirname(path.dirname(path.abspath(__file__)))))
DATA_DIR = f"{PROJECT_DIR}/data"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
        },
    },
    "loggers": {
        "app": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        }
    },
}

DATABASE = {
    "default": {
        "name": f"{DATA_DIR}/database.sqlite",
    },
}

DB_MODULES = [
    "wallet.lib.coin",
    "wallet.lib.price",
    "wallet.lib.transaction",
    "wallet.lib.secret",
    "wallet.lib.wallet",
    "wallet.lib.utxo",
]

PRICE = {
    "coingecko_mappings": {
        "binancecoin": ["bsc"],
        "ethereum": ["eth"],
        "huobi-token": ["heco"],
        "okexchain": ["okt"],
    },
    "uniswap_configs_v2": {
        "eth": {
            "router_address": "0x7a250d5630b4cf539739df2c5dacb4c659f2488d",
            "base_token_address": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
            "media_token_addresses": [
                "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
                "0xdac17f958d2ee523a2206206994597c13d831ec7",
                "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
                "0x6b175474e89094c44da98b954eedeac495271d0f",
            ],
        },
        "bsc": {
            "router_address": "0x10ED43C718714eb63d5aA57B78B54704E256024E",
            "base_token_address": "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c",
            "media_token_addresses": [
                "0x2170ed0880ac9a755fd29b2688956bd959f933f8",
                "0x55d398326f99059ff775485246999027b3197955",
                "0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d",
                "0xe9e7cea3dedca5984780bafc599bd69add087d56",
                "0x1af3f329e8be154074d8769d1ffa4ee058b1dbc3",
                "0x7130d2a12b9bcbfae4f2634d864a1ee1ce3ead9c",
            ],
        },
        "heco": {
            "router_address": "0xed7d5f38c79115ca12fe6c0041abb22f0a06c300",
            "base_token_address": "0x5545153ccfca01fbd7dd11c0b23ba694d9509a6f",
            "media_token_addresses": [
                "0x66a79d23e58475d2738179ca52cd0b41d73f0bea",
                "0x64ff637fb478863b7468bc97d30a5bf3a428a1fd",
                "0xa71edc38d189767582c38a3145b5873052c3e47a",
            ],
        },
        "okt": {
            "router_address": "0x865bfde337c8afbfff144ff4c29f9404ebb22b15",
            "base_token_address": "0x8f8526dbfd6e38e3d8307702ca8469bae6c56c15",
            "media_token_addresses": [
                "0x382bb369d343125bfb2117af9c149795c6c65c50",
                "0x54e4622dc504176b3bb432dccaf504569699a7ff",
                "0xef71ca2ee68f45b9ad6f72fbdb33d707b872315c",
                "0xc946daf81b08146b1c7a8da2a851ddf2b3eaaf85",
            ],
        },
    },
    "uniswap_configs_v3": {},
}

# loading local_settings.py on project root
try:
    from local_settings import *  # noqa
except ImportError:
    pass
