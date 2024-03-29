CHAINS = [
    {
        "chain_code": "tbtc",
        "fee_coin": "tbtc",
        "shortname": "TBTC",
        "name": "Testnet",
        "chain_model": "utxo",
        "curve": "secp256k1",
        "chain_affinity": "btc",
        "qr_code_prefix": "bitcoin",
        "bip44_coin_type": 1,
        "bip44_last_hardened_level": "ACCOUNT",
        "bip44_auto_increment_level": "ACCOUNT",
        "bip44_target_level": "ADDRESS_INDEX",
        "default_address_encoding": "P2WPKH-P2SH",
        "chain_id": None,
        "bip44_purpose_options": {"P2PKH": 44, "P2WPKH-P2SH": 49, "P2WPKH": 84},
        "fee_price_decimals_for_legibility": 0,
        "nonce_supported": False,
        "dust_threshold": 546,
        "coins": [
            {
                "code": "tbtc",
                "symbol": "TBTC",
                "name": "Bitcoin TestNet3",
                "decimals": 8,
                "icon": "https://onekey.243096.com/onekey/images/token/btc/BTC.png",
            }
        ],
        "clients": [
            {"class": "BlockBook", "url": "https://tbtc1.trezor.io"},
            {"class": "BlockBook", "url": "https://tbtc2.trezor.io"},
        ],
    },
    {
        "chain_code": "teth",
        "fee_coin": "teth",
        "shortname": "TETH",
        "name": "Ethereum Ropsten Test Network",
        "chain_model": "account",
        "curve": "secp256k1",
        "chain_affinity": "eth",
        "qr_code_prefix": "ethereum",
        "bip44_coin_type": 60,
        "bip44_last_hardened_level": "ACCOUNT",
        "bip44_auto_increment_level": "ADDRESS_INDEX",
        "bip44_target_level": "ADDRESS_INDEX",
        "default_address_encoding": None,
        "chain_id": "3",
        "bip44_purpose_options": {},
        "fee_price_decimals_for_legibility": 9,
        "nonce_supported": True,
        "coins": [
            {
                "code": "teth",
                "symbol": "TETH",
                "name": "Ethereum Ropsten Test Network",
                "decimals": 18,
                "icon": "https://onekey.243096.com/onekey/images/token/eth/ETH.png",
            }
        ],
        "clients": [
            {"class": "Geth", "url": "https://ropsten.infura.io/v3/f001ce716b6e4a33a557f74df6fe8eff"},
            {"class": "BlockBook", "url": "https://ropsten10.trezor.io"},
            {
                "class": "Etherscan",
                "url": "https://api-ropsten.etherscan.io",
                "api_keys": ["R796P9T31MEA24P8FNDZBCA88UHW8YCNVW"],
            },
        ],
    },
    {
        "chain_code": "tbsc",
        "fee_coin": "tbsc",
        "shortname": "TBSC",
        "name": "Binance Smart Chain Test Network",
        "chain_model": "account",
        "curve": "secp256k1",
        "chain_affinity": "eth",
        "qr_code_prefix": "bsc",
        "bip44_coin_type": 60,
        "bip44_last_hardened_level": "ACCOUNT",
        "bip44_auto_increment_level": "ADDRESS_INDEX",
        "bip44_target_level": "ADDRESS_INDEX",
        "default_address_encoding": None,
        "chain_id": "97",
        "bip44_purpose_options": {},
        "fee_price_decimals_for_legibility": 9,
        "nonce_supported": True,
        "coins": [
            {
                "code": "tbsc",
                "symbol": "TBNB",
                "name": "Binance Smart Chain Test Network",
                "decimals": 18,
                "icon": "https://onekey.243096.com/onekey/images/token/bsc/BSC.png",
            }
        ],
        "clients": [{"class": "Geth", "url": "https://data-seed-prebsc-2-s1.binance.org:8545"}],
    },
    {
        "chain_code": "theco",
        "fee_coin": "theco",
        "shortname": "THECO",
        "name": "Fork Huobi ECO Chain",
        "chain_model": "account",
        "curve": "secp256k1",
        "chain_affinity": "eth",
        "qr_code_prefix": "heco",
        "bip44_coin_type": 60,
        "bip44_last_hardened_level": "ACCOUNT",
        "bip44_auto_increment_level": "ADDRESS_INDEX",
        "bip44_target_level": "ADDRESS_INDEX",
        "default_address_encoding": None,
        "chain_id": "128",
        "bip44_purpose_options": {},
        "fee_price_decimals_for_legibility": 9,
        "nonce_supported": True,
        "coins": [
            {
                "code": "theco",
                "symbol": "THT",
                "name": "Huobi ECO Chain Test Network",
                "decimals": 18,
                "icon": "https://onekey.243096.com/onekey/images/token/heco/HECO.png",
            }
        ],
        "clients": [{"class": "Geth", "url": "https://testnode.onekey.so/heco"}],
    },
    {
        "chain_code": "tokt",
        "fee_coin": "tokt",
        "shortname": "TOKT",
        "name": "OKExChain Testnet",
        "chain_model": "account",
        "curve": "secp256k1",
        "chain_affinity": "eth",
        "qr_code_prefix": "okt",
        "bip44_coin_type": 60,
        "bip44_last_hardened_level": "ACCOUNT",
        "bip44_auto_increment_level": "ADDRESS_INDEX",
        "bip44_target_level": "ADDRESS_INDEX",
        "default_address_encoding": None,
        "chain_id": "65",
        "bip44_purpose_options": {},
        "fee_price_decimals_for_legibility": 9,
        "nonce_supported": True,
        "coins": [
            {
                "code": "tokt",
                "symbol": "TOKT",
                "name": "OKExChain Testnet",
                "decimals": 18,
                "icon": "https://onekey.243096.com/onekey/images/token/okt/OKT.png",
            }
        ],
        "clients": [{"class": "Geth", "url": "https://exchaintestrpc.okex.org"}],
    },
]
