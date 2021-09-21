from typing import List

CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"


def _b32encode(inputs: List[int]) -> str:
    out = ""
    for char_code in inputs:
        out += CHARSET[char_code]
    return out


def _b32decode(inputs: str) -> List[int]:
    out = list()
    for letter in inputs:
        out.append(CHARSET.find(letter))
    return out


def _polymod(values):
    chk = 1
    generator = [
        (0x01, 0x98F2BC8E61),
        (0x02, 0x79B76D99E2),
        (0x04, 0xF33E5FB3C4),
        (0x08, 0xAE2EABE2A8),
        (0x10, 0x1E4F43E470),
    ]
    for value in values:
        top = chk >> 35
        chk = ((chk & 0x07FFFFFFFF) << 5) ^ value
        for i in generator:
            if top & i[0] != 0:
                chk ^= i[1]
    return chk ^ 1


def _prefix_expand(prefix):
    return [ord(x) & 0x1F for x in prefix] + [0]


def _verify_checksum(prefix, payload):
    return _polymod(_prefix_expand(prefix) + payload) == 0


def _calculate_checksum(prefix, payload):
    poly = _polymod(_prefix_expand(prefix) + payload + [0, 0, 0, 0, 0, 0, 0, 0])
    out = list()
    for i in range(8):
        out.append((poly >> 5 * (7 - i)) & 0x1F)
    return out


def _convert_bits(data, from_bits, to_bits, pad=True):
    acc = 0
    bits = 0
    ret = []
    max_v = (1 << to_bits) - 1
    max_acc = (1 << (from_bits + to_bits - 1)) - 1

    for value in data:
        if value < 0 or (value >> from_bits):
            return None
        acc = ((acc << from_bits) | value) & max_acc
        bits += from_bits
        while bits >= to_bits:
            bits -= to_bits
            ret.append((acc >> bits) & max_v)

    if pad:
        if bits:
            ret.append((acc << (to_bits - bits)) & max_v)
    elif bits >= from_bits or ((acc << (to_bits - bits)) & max_v):
        return None

    return ret


def to_cash_address(prefix: str, pubkey_hash: bytes, version: int = 0) -> str:
    payload = [version, *pubkey_hash]
    payload = _convert_bits(payload, 8, 5)
    checksum = _calculate_checksum(prefix, payload)
    return prefix + ":" + _b32encode(payload + checksum)


def export_pubkey_hash(address: str) -> bytes:
    _, base32_str = address.split(":")
    payload = _b32decode(base32_str)
    converted = _convert_bits(payload, 5, 8)
    return bytes(converted[1:21])


def is_valid_cash_address(address: str) -> bool:
    prefix, base32_str = address.split(":")
    payload = _b32decode(base32_str)
    if not _verify_checksum(prefix, payload):
        return False
    converted = _convert_bits(payload, 5, 8)
    version = converted[0]
    return version == 0
