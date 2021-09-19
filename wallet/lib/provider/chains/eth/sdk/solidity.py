import re
from typing import Any, Literal, Optional, Sequence, Union

from wallet.lib.basic.functional.require import require
from wallet.lib.provider.chains.eth.sdk import utils

END_BRACKETS_OF_ARRAY_TYPE_REGEX = re.compile(r"\[[^]]*\]$")
END_NUMBER_OF_TYPE_REGEX = re.compile(r"^\D+(\d*)$")


def is_array_type(abi_type: str) -> bool:
    return abi_type.endswith("]")


def parse_sub_type_of_array_type(abi_type: str) -> str:
    return END_BRACKETS_OF_ARRAY_TYPE_REGEX.sub("", abi_type, 1)


def parse_size_of_array_type(abi_type: str) -> Union[Literal["dynamic"], int]:
    inner_brackets = END_BRACKETS_OF_ARRAY_TYPE_REGEX.search(abi_type).group(0).strip("[]")
    if not inner_brackets:
        return "dynamic"

    return int(inner_brackets)


def parse_type_n(abi_type: str) -> Optional[int]:
    num_str = END_NUMBER_OF_TYPE_REGEX.search(abi_type).group(1)
    if not num_str:
        return None

    return int(num_str)


def parse_int(value: Any) -> int:
    if isinstance(value, str) and value.startswith("0x"):
        return int(value, base=16)
    else:
        return int(value)


def solidity_encode_value(abi_type: str, value: Any, bit_size: int = None) -> bytes:
    if is_array_type(abi_type):
        require(isinstance(value, Sequence), f"Invalid {abi_type}: {repr(value)}")
        sub_type = parse_sub_type_of_array_type(abi_type)

        if not is_array_type(sub_type):
            array_size = parse_size_of_array_type(abi_type)
            require(
                array_size == "dynamic" or array_size == len(value),
                f"Elements exceed array size. expected: {array_size}, actual: {len(value)}, value: {repr(value)}",
            )

        buffer = bytearray()
        for i in value:
            buffer.extend(solidity_encode_value(sub_type, i, bit_size=256))

        return buffer
    elif abi_type == "string":
        require(isinstance(value, str), f"Invalid {abi_type}: {repr(value)}")
        return value.encode("utf-8")
    elif abi_type == "bool":
        require(isinstance(value, bool), f"Invalid {abi_type}: {repr(value)}")
        bit_size = bit_size or 8
        return bytes([1 if value else 0]).rjust(bit_size >> 3, bytes(1))
    elif abi_type == "address":
        require(
            isinstance(value, str) and value.startswith("0x") and len(value) == 42, f"Invalid {abi_type}: {repr(value)}"
        )
        byte_size = bit_size >> 3 if bit_size else 20
        return bytes.fromhex(utils.remove_0x_prefix(value)).rjust(byte_size, bytes(1))
    elif abi_type == "bytes":
        require(isinstance(value, (bytes, bytearray, str)), f"Invalid {abi_type}: {repr(value)}")
        return bytes.fromhex(utils.remove_0x_prefix(value)) if isinstance(value, str) else value
    elif abi_type.startswith("bytes"):
        byte_size = parse_type_n(abi_type)
        require(byte_size and 1 <= byte_size <= 32, f"Invalid bytes<N> width: {byte_size}")
        require(isinstance(value, (bytes, bytearray, str)), f"Invalid {abi_type}: {repr(value)}")
        value = bytes.fromhex(utils.remove_0x_prefix(value)) if isinstance(value, str) else value
        require(
            len(value) <= byte_size,
            f"Value exceed byte size. expected: {byte_size}, actual: {len(value)}, value: {repr(value)}",
        )
        return value.ljust(byte_size, bytes(1))  # padding left here only
    elif abi_type.startswith("uint"):
        bit_size = bit_size or parse_type_n(abi_type) or 256
        require(8 <= bit_size <= 256 and bit_size % 8 == 0, f"Invalid uint<N> width: {bit_size}")
        require(isinstance(value, (int, str)), f"Invalid {abi_type}: {repr(value)}")
        value = parse_int(value)
        require(value >= 0 and value.bit_length() <= bit_size, f"Invalid {abi_type}: {repr(value)}")
        return utils.int_to_big_endian(value).rjust(bit_size >> 3, bytes(1))
    elif abi_type.startswith("int"):
        bit_size = bit_size or parse_type_n(abi_type) or 256
        require(8 <= bit_size <= 256 and bit_size % 8 == 0, f"Invalid int<N> width: {bit_size}")
        require(isinstance(value, (int, str)), f"Invalid {abi_type}: {repr(value)}")
        value = parse_int(value)
        require(
            value.bit_length() <= bit_size,
            f"Value exceed bit size. expected: {bit_size}, actual: {value.bit_length()}, value: {repr(value)}",
        )
        value = value if value >= 0 else (1 << bit_size) + value
        return utils.int_to_big_endian(value).rjust(bit_size >> 3, bytes(1))

    raise Exception(f"Unsupported or invalid type: {repr(abi_type)}")


def solidity_pack(types: Sequence[str], values: Sequence[Any]) -> bytes:
    require(len(types) == len(values), "Number of types are not matching the values")

    buffer = bytearray()
    for abi_type, value in zip(types, values):
        buffer.extend(solidity_encode_value(abi_type, value))

    return buffer


def solidity_sha3(types: Sequence[str], values: Sequence[Any]) -> bytes:
    return utils.keccak(solidity_pack(types, values))
