import json
from enum import IntEnum
from typing import Any, Callable, Iterable, Sequence, Tuple

import eth_abi
from eth_account._utils.structured_data.hashing import encode_type as encode_primary_type

from tilapia.lib.basic.functional.require import require
from tilapia.lib.provider.chains.eth.sdk import solidity, utils

_LEGACY_EIP712_ITEM_FIELD_NAMES = {"type", "name", "value"}  # V1
_STANDARD_EIP712_FIELD_NAMES = {"types", "primaryType", "domain", "message"}  # V3 and V4


class MessageType(IntEnum):
    """MessageType supported."""

    NORMAL = 0
    TYPE_DATA_V1 = 1
    TYPE_DATA_EIP712 = 2


def _to_buffer(value: str) -> bytes:
    if value.startswith("0x") and utils.is_hexstr(value):
        value = utils.remove_0x_prefix(value)
        if len(value) & 1 == 1:
            value = "0" + value  # pad to even

        return utils.decode_hex(value)
    else:
        return value.encode()


def _hash_personal_message(message: str) -> bytes:
    message_bytes = _to_buffer(message)
    preamble = f"\x19Ethereum Signed Message:\n{len(message_bytes)}"
    message_bytes = preamble.encode() + message_bytes

    return utils.keccak(message_bytes)


def _hash_legacy_typed_data_message(data: list) -> bytes:
    values, types, schemas = [], [], []

    for item in data:
        solidity_type, name, value = item["type"], item["name"], item["value"]
        require(name)

        values.append(value)
        types.append(solidity_type)
        schemas.append(f"{solidity_type} {name}")

    return solidity.solidity_sha3(
        ("bytes32", "bytes32"),
        (
            solidity.solidity_sha3(["string"] * len(data), schemas),
            solidity.solidity_sha3(types, values),
        ),
    )


def _encode_and_hash_data(primary_type: str, data: dict, types: dict, type_value_pair_generator: Callable) -> bytes:
    data_types, data_values = zip(*type_value_pair_generator(primary_type, data, types))
    return utils.keccak(eth_abi.encode_abi(data_types, data_values))


def _normalized_value(field_type: str, value: Any) -> Any:
    if not field_type or not value:
        return value

    if field_type.startswith("bytes") and isinstance(value, str):
        value = bytes.fromhex(utils.remove_0x_prefix(value))
    elif (field_type.startswith("int") or field_type.startswith("uint")) and isinstance(value, str):
        value = int(value, base=16 if value.startswith("0x") else 10)

    return value


def _generate_v3_type_value_pair(primary_type: str, data: dict, types: dict) -> Iterable[Tuple[str, Any]]:
    yield "bytes32", utils.keccak(text=encode_primary_type(primary_type, types))

    for field in types[primary_type]:
        field_name, field_type = field.get("name"), field.get("type")
        value = data.get(field_name)
        value = _normalized_value(field_type, value)

        if value is None:
            continue
        elif solidity.is_array_type(field_type):
            raise Exception("Arrays are unimplemented in V3, use V4 extension")
        elif types.get(field_type) is not None:
            yield "bytes32", _encode_and_hash_data(field_type, value, types, _generate_v3_type_value_pair)
        elif field_type in ("bytes", "string"):
            value = utils.keccak(solidity.solidity_encode_value(field_type, value))
            yield "bytes32", value
        else:
            yield field_type, value


def _generate_v4_type_value_pair(primary_type: str, data: dict, types: dict) -> Iterable[Tuple[str, Any]]:
    yield "bytes32", utils.keccak(text=encode_primary_type(primary_type, types))

    def _encode_field(field_name: str, field_type: str, value: Any) -> Tuple[str, Any]:
        value = _normalized_value(field_type, value)

        if types.get(field_type) is not None:
            return "bytes32", (
                bytes(32)
                if value is None
                else _encode_and_hash_data(field_type, value, types, _generate_v4_type_value_pair)
            )
        elif value is None:
            raise Exception(f"Missing value for field {field_name} of type {field_type}")
        elif solidity.is_array_type(field_type):
            require(isinstance(value, Sequence), f"Invalid {field_type}: {repr(value)}")
            sub_type = solidity.parse_sub_type_of_array_type(field_type)
            sub_types, sub_values = zip(*(_encode_field(field_name, sub_type, i) for i in value))
            return "bytes32", utils.keccak(eth_abi.encode_abi(sub_types, sub_values))
        elif field_type in ("bytes", "string"):
            value = utils.keccak(solidity.solidity_encode_value(field_type, value))
            return "bytes32", value
        else:
            return field_type, value

    for field in types[primary_type]:
        yield _encode_field(field.get("name"), field.get("type"), data.get(field.get("name")))


def _hash_eip712_message(data: dict) -> bytes:
    buffer = bytearray()
    buffer.extend(b"\x19\x01")
    domain_hash, message_hash = _eip712_encode(data)
    buffer.extend(domain_hash)
    if message_hash:
        buffer.extend(message_hash)
    return utils.keccak(buffer)


def _eip712_encode(data: dict) -> Tuple[bytes, bytes]:
    version = data.pop("__version__", 4)  # Non-standard field
    if version == 3:
        type_value_pair_generator = _generate_v3_type_value_pair
    else:
        type_value_pair_generator = _generate_v4_type_value_pair
    domain_hash = _encode_and_hash_data("EIP712Domain", data["domain"], data["types"], type_value_pair_generator)
    message_hash = None
    if data["primaryType"] != "EIP712Domain":
        message_hash = _encode_and_hash_data(
            data["primaryType"], data["message"], data["types"], type_value_pair_generator
        )
    return domain_hash, message_hash


def _hash_typed_data_message(message: str, message_type: MessageType) -> bytes:
    data = json.loads(message)

    if message_type == MessageType.TYPE_DATA_V1:
        return _hash_legacy_typed_data_message(data)
    elif message_type == MessageType.TYPE_DATA_EIP712:
        return _hash_eip712_message(data)

    raise Exception(f"Invalid typed data message. message: {message}")


def classify_message_type(message: str) -> MessageType:
    try:
        data = json.loads(message)
    except ValueError:
        return MessageType.NORMAL
    if isinstance(data, list) and all(
        isinstance(item, dict) and _LEGACY_EIP712_ITEM_FIELD_NAMES.issubset(item.keys()) for item in data
    ):  # V1?
        return MessageType.TYPE_DATA_V1
    elif isinstance(data, dict) and _STANDARD_EIP712_FIELD_NAMES.issubset(data.keys()):  # V3 or V4?
        return MessageType.TYPE_DATA_EIP712
    return MessageType.NORMAL


def hash_message(message: str) -> bytes:
    try:
        if (
            message.startswith("0x") and len(message) == 66 and utils.is_hexstr(message)
        ):  # Only a hexadecimal string starting with 0x and having a length of 66, that is, 32 bytes
            buffer = bytes.fromhex(utils.remove_0x_prefix(message))
        else:
            message_type = classify_message_type(message)
            if message_type == MessageType.NORMAL:
                buffer = _hash_personal_message(message)
            else:
                buffer = _hash_typed_data_message(message, message_type)
        require(len(buffer) == 32, f"Size of message hash buffer should be 32, but now is {len(buffer)}")
        return buffer
    except Exception as e:
        raise ValueError(f"Invalid message. caused by: {repr(e)}, message: {message}") from e


def encode_eip712_message(message: str) -> Tuple[bytes, bytes]:
    """Make sure the message is valid version before usage."""
    require(classify_message_type(message) == MessageType.TYPE_DATA_EIP712, "Invalid message type")
    return _eip712_encode(json.loads(message))
