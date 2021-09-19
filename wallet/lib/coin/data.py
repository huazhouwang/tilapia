from dataclasses import dataclass, field
from enum import IntEnum, unique
from typing import List, Optional

from wallet.lib.basic import bip44
from wallet.lib.basic.dataclass.dataclass import DataClassMixin
from wallet.lib.secret import data as secret_data


@unique
class ChainModel(IntEnum):
    UTXO = 10
    ACCOUNT = 20


@dataclass
class ChainInfo(DataClassMixin):
    chain_code: str  # unique chain coin
    fee_coin: str  # which coin is used to provide fee (omni chain uses btc, neo uses neo_gas etc.)
    name: str  # full name of chain, please keep the same with hardware wallet if supports hardware
    shortname: str  # short name of chain
    chain_model: ChainModel  # model of chain (UTXO, Account etc.)
    curve: secret_data.CurveEnum  # curve type
    chain_affinity: str  # mark chain affinity
    bip44_coin_type: int  # coin_type of bip44 path
    clients: List[dict] = field(default_factory=list)
    bip44_last_hardened_level: bip44.BIP44Level = (
        bip44.BIP44Level.ACCOUNT
    )  # hardened to 'ACCOUNT' level as default, but hardened to 'ADDRESS_INDEX' level in ED25519 curve
    bip44_auto_increment_level: bip44.BIP44Level = (
        bip44.BIP44Level.ADDRESS_INDEX
    )  # Auto increase 'ADDRESS_INDEX' level to derive new address (options: ACCOUNT, CHANGE, ADDRESS_INDEX)
    bip44_target_level: bip44.BIP44Level = (
        bip44.BIP44Level.ADDRESS_INDEX
    )  # Derive to 'ADDRESS_INDEX' as default (options: ACCOUNT, CHANGE, ADDRESS_INDEX)
    default_address_encoding: Optional[str] = None
    nonce_supported: bool = False
    chain_id: Optional[str] = None  # optional, identify multi forked chains by chain_id (use by eth etc.)
    bip44_purpose_options: dict = field(default_factory=dict)
    fee_price_decimals_for_legibility: int = 0  # (gwei in eth etc.)
    impl_options: dict = field(default_factory=dict)  # customizable options that differ between implemetations
    dust_threshold: int = 0
    blocktime_seconds: int = 0
    qr_code_prefix: str = ""  # Deprecated QR code prefix of address

    def choose_address_encoding(self, purpose: int = None) -> Optional[str]:
        if purpose is not None and self.bip44_purpose_options:
            for encoding, _purpose in self.bip44_purpose_options.items():
                if purpose == _purpose:
                    return encoding

        return self.default_address_encoding


@dataclass
class CoinInfo(DataClassMixin):
    code: str  # unique code
    chain_code: str  # which chain does it belong to

    name: str  # full name of coin
    symbol: str  # symbol of coin

    decimals: int  # decimals of coin
    icon: Optional[str] = None  # icon url of coin

    token_address: Optional[str] = None  # optional, used by tokens
