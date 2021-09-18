import eth_typing
import eth_utils
from eth_utils import (  # noqa F401
    big_endian_to_int,
    decode_hex,
    int_to_big_endian,
    is_address,
    is_hexstr,
    keccak,
    to_checksum_address,
)


def add_0x_prefix(value: str) -> str:
    return eth_utils.add_0x_prefix(eth_typing.HexStr(value))


def remove_0x_prefix(value: str) -> str:
    return eth_utils.remove_0x_prefix(eth_typing.HexStr(value))
